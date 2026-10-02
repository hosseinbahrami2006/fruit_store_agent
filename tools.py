from decimal import Decimal

from calculator import calculate
from inventory import (
    load_inventory,
    normalize_name,
    save_inventory,
    validate_basket,
)


TOOL_SCHEMAS = [
    {
        "name": "list_products",
        "description": "Read all product names, prices, and stock.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_product",
        "description": "Read the price and available stock of one fruit.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
            },
            "required": ["product_name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "calculator",
        "description": (
            "Create an invoice quote for a complete basket. "
            "Read trusted prices, validate stock, and calculate totals. "
            "Reject the whole invoice if any item is invalid."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_name": {"type": "string"},
                            "quantity_kg": {
                                "type": "number",
                                "exclusiveMinimum": 0,
                            },
                        },
                        "required": ["product_name", "quantity_kg"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["items"],
            "additionalProperties": False,
        },
    },
]


def list_products():
    return load_inventory()


def get_product(product_name):
    inventory = load_inventory()
    key = normalize_name(product_name)

    for product in inventory["products"]:
        if normalize_name(product["name"]) == key:
            return {
                "currency": inventory["currency"],
                "quantity_unit": "kg",
                "product": product,
            }

    return {"error": f"Product '{product_name}' was not found."}


def calculator(items):
    """Validate the basket, then invoke the separate calculator."""
    inventory = load_inventory()
    validated = validate_basket(items, inventory)

    return calculate(validated, inventory["currency"])


def confirm_order(quote):
    """
    Revalidate the pending quote before updating inventory.

    All checks happen before saving any stock changes.
    """
    if quote is None:
        raise ValueError("There is no pending order to confirm.")

    inventory = load_inventory()
    validated = validate_basket(quote["items"], inventory)

    if inventory["currency"] != quote["currency"]:
        raise ValueError(
            "The currency has changed. Request a new invoice quote."
        )

    quoted_prices = {
        normalize_name(item["product_name"]): Decimal(
            item["price_per_kg"]
        )
        for item in quote["items"]
    }

    for item in validated:
        product = item["product"]
        key = normalize_name(product["name"])
        current_price = Decimal(str(product["price_per_kg"]))

        if current_price != quoted_prices[key]:
            raise ValueError(
                f"The price of {product['name']} has changed. "
                "Request a new invoice quote."
            )

    # Update the in-memory copy only after every check passes.
    for item in validated:
        product = item["product"]

        remaining_stock = (
            Decimal(str(product["stock_kg"])) - item["quantity"]
        )

        product["stock_kg"] = str(remaining_stock)

    save_inventory(inventory)
    return quote


def format_invoice(quote, confirmed=False):
    title = "Confirmed invoice:" if confirmed else "Invoice quote:"
    lines = [title]

    for item in quote["items"]:
        lines.append(
            f"- {item['product_name']}: "
            f"{item['quantity_kg']} kg x "
            f"{item['price_per_kg']} {quote['currency']}/kg "
            f"= {item['subtotal']} {quote['currency']}"
        )

    lines.append(f"\nTotal: {quote['total']} {quote['currency']}")

    if confirmed:
        lines.append("Order confirmed. Inventory has been updated.")
    else:
        lines.append(
            "Stock has not been reserved or reduced.\n"
            "Type 'confirm order' to complete this order, "
            "or 'cancel order' to discard it."
        )

    return "\n".join(lines)