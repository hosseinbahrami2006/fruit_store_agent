
import json  # Read and write JSON.
import os  # Use operating-system functions.
import tempfile  # Create temporary files.
from decimal import Decimal, InvalidOperation  # Handle decimal numbers.
from pathlib import Path  # Work with file paths.


INVENTORY_PATH = Path(__file__).resolve().parent / "fruits.json"  # Inventory location.


def normalize_name(name):  # Standardize a fruit name.
    name = name.strip()  # Remove surrounding spaces.
    name = name.casefold()  # Normalize uppercase and lowercase.

    aliases = {  # Match plural names to singular names.
        "apples": "apple",  # Plural of apple.
        "bananas": "banana",  # Plural of banana.
        "oranges": "orange",  # Plural of orange.
        "grapes": "grape",  # Plural of grape.
        "mangoes": "mango",  # Plural of mango.
        "mangos": "mango",  # Alternative plural.
        "pears": "pear",  # Plural of pear.
        "peaches": "peach",  # Plural of peach.
        "kiwis": "kiwi",  # Plural of kiwi.
        "pineapples": "pineapple",  # Plural of pineapple.
        "strawberries": "strawberry",  # Plural of strawberry.
    }  # End of aliases.

    if name in aliases:  # Check for a known plural.
        return aliases[name]  # Return its singular name.

    return name  # Keep other names unchanged.


def parse_decimal(value, label, allow_zero=False):  # Validate a number.
    try:  # Attempt the conversion.
        number = Decimal(str(value))  # Convert to Decimal.
    except (InvalidOperation, ValueError):  # Handle invalid numbers.
        raise ValueError(f"{label} must be a valid number.")  # Report the error.

    if allow_zero:  # Check whether zero is allowed.
        minimum_valid = number >= 0  # Accept zero or positive numbers.
    else:  # Zero is not allowed.
        minimum_valid = number > 0  # Accept positive numbers only.

    if not number.is_finite() or not minimum_valid:  # Reject invalid values.
        if allow_zero:  # Choose the correct requirement.
            condition = "nonnegative"  # Zero is allowed.
        else:  # Only positive numbers are allowed.
            condition = "positive"  # Zero is not allowed.

        raise ValueError(f"{label} must be finite and {condition}.")  # Report the error.

    return number  # Return the validated Decimal.


def load_inventory():  # Read and validate the inventory.
    with INVENTORY_PATH.open("r", encoding="utf-8") as file:  # Open the JSON file.
        data = json.load(file)  # Read the inventory data.

    if not isinstance(data, dict):  # Check the main structure.
        raise ValueError("Invalid inventory file structure.")  # Report invalid structure.

    if not isinstance(data.get("products"), list):  # Check the products list.
        raise ValueError("Invalid inventory file structure.")  # Report invalid structure.

    if not isinstance(data.get("currency"), str):  # Check the currency type.
        raise ValueError("The inventory must specify a currency.")  # Report missing currency.

    if data.get("quantity_unit") != "kg":  # Check the quantity unit.
        raise ValueError("The inventory quantity unit must be kg.")  # Report invalid unit.

    names = set()  # Track unique product names.

    for product in data["products"]:  # Check every product.
        name = product["name"]  # Read the product name.

        if not isinstance(name, str):  # Check the name type.
            raise ValueError("Every product must have a valid name.")  # Report invalid name.

        if not name.strip():  # Check for an empty name.
            raise ValueError("Every product must have a valid name.")  # Report empty name.

        key = normalize_name(name)  # Standardize the name.

        if key in names:  # Check for duplicate products.
            raise ValueError(f"Duplicate inventory product: {name}.")  # Report the duplicate.

        names.add(key)  # Remember this product name.

        parse_decimal(product["price_per_kg"], f"Price for {name}")  # Validate the price.
        parse_decimal(product["stock_kg"], f"Stock for {name}", allow_zero=True)  # Validate stock.

    return data  # Return the validated inventory.


def save_inventory(data):  # Save the inventory safely.
    temporary_path = None  # No temporary file exists yet.

    try:  # Always run cleanup afterward.
        with tempfile.NamedTemporaryFile(  # Create a temporary file.
            mode="w",  # Open for writing.
            encoding="utf-8",  # Use UTF-8 text.
            dir=INVENTORY_PATH.parent,  # Use the inventory folder.
            prefix="inventory_",  # Set the filename prefix.
            suffix=".tmp",  # Set the filename ending.
            delete=False,  # Keep the file after closing.
        ) as file:  # Access the temporary file.
            temporary_path = Path(file.name)  # Store its path.
            json.dump(data, file, indent=2)  # Write formatted JSON.
            file.write("\n")  # Add a final newline.
            file.flush()  # Flush Python's write buffer.
            os.fsync(file.fileno())  # Synchronize the file to disk.

        os.replace(temporary_path, INVENTORY_PATH)  # Replace the inventory atomically.

    finally:  # Clean up even after an error.
        if temporary_path is not None:  # Check whether a file was created.
            if temporary_path.exists():  # Check whether it still exists.
                temporary_path.unlink()  # Delete the temporary file.


def validate_basket(items, inventory):  # Validate the complete basket.
    if not isinstance(items, list):  # Check the basket type.
        raise ValueError("Provide at least one product and its quantity.")  # Report invalid basket.

    if not items:  # Check for an empty basket.
        raise ValueError("Provide at least one product and its quantity.")  # Report empty basket.

    quantities = {}  # Store each product's total quantity.

    for item in items:  # Check each basket item.
        if not isinstance(item, dict):  # Check the item type.
            raise ValueError("Each basket item must be an object.")  # Report invalid item.

        name = item.get("product_name")  # Read the requested name.

        if not isinstance(name, str):  # Check the name type.
            raise ValueError("Every basket item needs a product name.")  # Report invalid name.

        if not name.strip():  # Check for an empty name.
            raise ValueError("Every basket item needs a product name.")  # Report empty name.

        quantity = parse_decimal(  # Validate the requested quantity.
            item.get("quantity_kg"),  # Read the quantity.
            f"Quantity for {name}",  # Label possible errors.
        )  # Store the validated Decimal.

        key = normalize_name(name)  # Standardize the product name.

        if key not in quantities:  # Check for the first occurrence.
            quantities[key] = Decimal("0")  # Start its total at zero.

        quantities[key] = quantities[key] + quantity  # Add the requested quantity.

    products = {}  # Map names to inventory records.

    for product in inventory["products"]:  # Read every inventory product.
        key = normalize_name(product["name"])  # Standardize its name.
        products[key] = product  # Store its inventory record.

    errors = []  # Collect basket errors.
    validated = []  # Collect valid products and quantities.

    for name, quantity in quantities.items():  # Check each combined quantity.
        product = products.get(name)  # Find the inventory product.

        if product is None:  # Check for an unknown product.
            errors.append(f"Product '{name}' was not found.")  # Record the error.
            continue  # Move to the next product.

        stock = Decimal(str(product["stock_kg"]))  # Read available stock.

        if quantity > stock:  # Check for insufficient stock.
            errors.append(  # Record the stock error.
                f"Insufficient stock for {product['name']}: "  # Identify the product.
                f"requested {quantity} kg; available {stock} kg."  # Show the quantities.
            )  # Finish recording the error.
            continue  # Move to the next product.

        validated.append({  # Store the valid basket item.
            "product": product,  # Keep the trusted product record.
            "quantity": quantity,  # Keep the combined quantity.
        })  # Add the item to the result.

    if errors:  # Reject the basket if any error exists.
        raise ValueError("\n".join(errors))  # Report all collected errors.

    return validated  # Return the fully validated basket.
