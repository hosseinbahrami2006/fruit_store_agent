import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path


INVENTORY_PATH = Path(__file__).resolve().parent / "fruits.json"


def normalize_name(name):
    """Normalize a fruit name and map known plural forms to singular."""
    name = name.strip()
    name = name.casefold()

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

    if name in aliases:
        return aliases[name]

    return name


def parse_decimal(value, label, allow_zero=False):
    """Convert a value to Decimal and validate its sign and finiteness."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid number.")

    if allow_zero:
        minimum_valid = number >= 0
    else:
        minimum_valid = number > 0

    if not number.is_finite() or not minimum_valid:
        if allow_zero:
            condition = "nonnegative"
        else:
            condition = "positive"

        raise ValueError(f"{label} must be finite and {condition}.")

    return number


def load_inventory():
    """Load the inventory file and validate its structure and product data."""
    with INVENTORY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Invalid inventory file structure.")

    if not isinstance(data.get("products"), list):
        raise ValueError("Invalid inventory file structure.")

    if not isinstance(data.get("currency"), str):
        raise ValueError("The inventory must specify a currency.")

    if data.get("quantity_unit") != "kg":
        raise ValueError("The inventory quantity unit must be kg.")

    names = set()

    for product in data["products"]:
        name = product["name"]

        if not isinstance(name, str):
            raise ValueError("Every product must have a valid name.")

        if not name.strip():
            raise ValueError("Every product must have a valid name.")

        key = normalize_name(name)

        if key in names:
            raise ValueError(f"Duplicate inventory product: {name}.")

        names.add(key)

        parse_decimal(product["price_per_kg"], f"Price for {name}")
        parse_decimal(product["stock_kg"], f"Stock for {name}", allow_zero=True)

    return data


def save_inventory(data):
    """Write inventory data to a temporary file and replace the original."""
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
        if temporary_path is not None:
            if temporary_path.exists():
                temporary_path.unlink()


def validate_basket(items, inventory):
    """Validate basket items, combine duplicate products, and check stock."""
    if not isinstance(items, list):
        raise ValueError("Provide at least one product and its quantity.")

    if not items:
        raise ValueError("Provide at least one product and its quantity.")

    quantities = {}

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each basket item must be an object.")

        name = item.get("product_name")

        if not isinstance(name, str):
            raise ValueError("Every basket item needs a product name.")

        if not name.strip():
            raise ValueError("Every basket item needs a product name.")

        quantity = parse_decimal(
            item.get("quantity_kg"),
            f"Quantity for {name}",
        )

        key = normalize_name(name)

        if key not in quantities:
            quantities[key] = Decimal("0")

        quantities[key] = quantities[key] + quantity

    products = {}

    for product in inventory["products"]:
        key = normalize_name(product["name"])
        products[key] = product

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
