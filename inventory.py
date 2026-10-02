import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path


# Change this path if the inventory file is stored elsewhere.
INVENTORY_PATH = Path(__file__).resolve().parent / "fruits.json"


def normalize_name(name):
    """Convert common plural fruit names to singular names."""
    name = name.strip().casefold()

    aliases = {
        "apples": "apple",
        "bananas": "banana",
        "oranges": "orange",
        "grapes": "grape",
        "mangoes": "mango",
        "mangos": "mango",
        "pears": "pear",
        "peaches": "peach",
        "kiwis": "kiwi",
        "pineapples": "pineapple",
        "strawberries": "strawberry",
    }

    return aliases.get(name, name)


def parse_decimal(value, label, allow_zero=False):
    """Validate a numeric value and return an exact Decimal."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid number.")

    minimum_valid = number >= 0 if allow_zero else number > 0

    if not number.is_finite() or not minimum_valid:
        condition = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{label} must be finite and {condition}.")

    return number


def load_inventory():
    """Read and validate the current inventory."""
    with INVENTORY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or not isinstance(
        data.get("products"), list
    ):
        raise ValueError("Invalid inventory file structure.")

    if not isinstance(data.get("currency"), str):
        raise ValueError("The inventory must specify a currency.")

    if data.get("quantity_unit") != "kg":
        raise ValueError("The inventory quantity unit must be kg.")

    names = set()

    for product in data["products"]:
        name = product["name"]

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every product must have a valid name.")

        key = normalize_name(name)

        if key in names:
            raise ValueError(f"Duplicate inventory product: {name}.")

        names.add(key)

        parse_decimal(product["price_per_kg"], f"Price for {name}")
        parse_decimal(
            product["stock_kg"],
            f"Stock for {name}",
            allow_zero=True,
        )

    return data


def save_inventory(data):
    """Replace the JSON file atomically to avoid partial writes."""
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=INVENTORY_PATH.parent,
            prefix="inventory_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, INVENTORY_PATH)

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def validate_basket(items, inventory):
    """
    Combine duplicate items and validate the entire basket.

    Return trusted product records and quantities.
    Do not issue a partial invoice if any item is invalid.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("Provide at least one product and its quantity.")

    quantities = {}

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each basket item must be an object.")

        name = item.get("product_name")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every basket item needs a product name.")

        quantity = parse_decimal(
            item.get("quantity_kg"),
            f"Quantity for {name}",
        )

        key = normalize_name(name)
        quantities[key] = quantities.get(key, Decimal("0")) + quantity

    products = {
        normalize_name(product["name"]): product
        for product in inventory["products"]
    }

    errors = []
    validated = []

    for name, quantity in quantities.items():
        product = products.get(name)

        if product is None:
            errors.append(f"Product '{name}' was not found.")
            continue

        stock = Decimal(str(product["stock_kg"]))

        if quantity > stock:
            errors.append(
                f"Insufficient stock for {product['name']}: "
                f"requested {quantity} kg; available {stock} kg."
            )
            continue

        validated.append({
            "product": product,
            "quantity": quantity,
        })

    if errors:
        raise ValueError("\n".join(errors))

    return validated