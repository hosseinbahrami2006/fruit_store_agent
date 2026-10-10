from decimal import Decimal  # Work with decimal numbers.

from calculator import calculate  # Import invoice calculation.
from inventory import (  # Import inventory functions.
    load_inventory,  # Read the inventory.
    normalize_name,  # Standardize product names.
    save_inventory,  # Save inventory changes.
    validate_basket,  # Check basket items.
)  # Finish the imports.


TOOL_SCHEMAS = [  # Describe the available tools.
    {  # Define the listing tool.
        "name": "list_products",  # Set the tool name.
        "description": "Read all product names, prices, and stock.",  # Explain its purpose.
        "parameters": {  # Define accepted inputs.
            "type": "object",  # Inputs must be an object.
            "properties": {},  # No inputs are needed.
            "additionalProperties": False,  # Reject extra inputs.
        },  # Finish the parameters.
    },  # Finish the listing tool.
    {  # Define the product lookup tool.
        "name": "get_product",  # Set the tool name.
        "description": "Read the price and available stock of one fruit.",  # Explain its purpose.
        "parameters": {  # Define accepted inputs.
            "type": "object",  # Inputs must be an object.
            "properties": {  # Define input fields.
                "product_name": {"type": "string"},  # Accept a product name.
            },  # Finish the input fields.
            "required": ["product_name"],  # Require the product name.
            "additionalProperties": False,  # Reject extra inputs.
        },  # Finish the parameters.
    },  # Finish the lookup tool.
    {  # Define the invoice tool.
        "name": "calculator",  # Set the tool name.
        "description": (  # Explain its purpose.
            "Create an invoice quote for a complete basket. "  # Describe the result.
            "Read trusted prices, validate stock, and calculate totals. "  # Describe the checks.
            "Reject the whole invoice if any item is invalid."  # Describe error handling.
        ),  # Finish the description.
        "parameters": {  # Define accepted inputs.
            "type": "object",  # Inputs must be an object.
            "properties": {  # Define input fields.
                "items": {  # Define the basket.
                    "type": "array",  # Accept a list of items.
                    "minItems": 1,  # Require at least one item.
                    "items": {  # Define each basket item.
                        "type": "object",  # Each item must be an object.
                        "properties": {  # Define item fields.
                            "product_name": {"type": "string"},  # Accept a product name.
                            "quantity_kg": {  # Define the quantity.
                                "type": "number",  # Accept a number.
                                "exclusiveMinimum": 0,  # Require more than zero.
                            },  # Finish the quantity.
                        },  # Finish the item fields.
                        "required": ["product_name", "quantity_kg"],  # Require both fields.
                        "additionalProperties": False,  # Reject extra fields.
                    },  # Finish the item definition.
                },  # Finish the basket definition.
            },  # Finish the input fields.
            "required": ["items"],  # Require the basket.
            "additionalProperties": False,  # Reject extra inputs.
        },  # Finish the parameters.
    },  # Finish the invoice tool.
]  # Finish the tool schemas.


def list_products():  # Return the complete inventory.
    return load_inventory()  # Read and return inventory data.


def get_product(product_name):  # Find one product.
    inventory = load_inventory()  # Read the latest inventory.
    key = normalize_name(product_name)  # Standardize the requested name.

    for product in inventory["products"]:  # Check each inventory product.
        if normalize_name(product["name"]) == key:  # Check for a matching name.
            return {  # Return the matching product.
                "currency": inventory["currency"],  # Include the currency.
                "quantity_unit": "kg",  # Include the quantity unit.
                "product": product,  # Include the product record.
            }  # Finish the result.

    return {"error": f"Product '{product_name}' was not found."}  # Report an unknown product.


def calculator(items):  # Validate and calculate a quote.
    inventory = load_inventory()  # Read the latest inventory.
    validated = validate_basket(items, inventory)  # Validate the complete basket.

    return calculate(validated, inventory["currency"])  # Return the calculated quote.


def confirm_order(quote):  # Check and confirm the pending order.
    if quote is None:  # Check for a missing quote.
        raise ValueError("There is no pending order to confirm.")  # Report the missing order.

    inventory = load_inventory()  # Read the latest inventory.
    validated = validate_basket(quote["items"], inventory)  # Recheck products and stock.

    if inventory["currency"] != quote["currency"]:  # Check for a currency change.
        raise ValueError(  # Reject the outdated quote.
            "The currency has changed. Request a new invoice quote."  # Explain the problem.
        )  # Finish the error.

    quoted_prices = {}  # Store prices from the quote.

    for item in quote["items"]:  # Read each quoted item.
        key = normalize_name(item["product_name"])  # Standardize its name.
        quoted_prices[key] = Decimal(item["price_per_kg"])  # Store its quoted price.

    for item in validated:  # Check each validated product.
        product = item["product"]  # Get the inventory record.
        key = normalize_name(product["name"])  # Standardize its name.
        current_price = Decimal(str(product["price_per_kg"]))  # Read its current price.

        if current_price != quoted_prices[key]:  # Check for a price change.
            raise ValueError(  # Reject the outdated quote.
                f"The price of {product['name']} has changed. "  # Identify the changed product.
                "Request a new invoice quote."  # Explain the next step.
            )  # Finish the error.

    for item in validated:  # Update stock after all checks pass.
        product = item["product"]  # Get the inventory record.

        remaining_stock = Decimal(str(product["stock_kg"]))  # Read the current stock.
        remaining_stock = remaining_stock - item["quantity"]  # Subtract the ordered quantity.

        product["stock_kg"] = str(remaining_stock)  # Store the remaining stock as text.

    save_inventory(inventory)  # Save all inventory changes.
    return quote  # Return the original quote.


def format_invoice(quote, confirmed=False):  # Build the invoice text.
    if confirmed:  # Check whether the order is confirmed.
        title = "Confirmed invoice:"  # Use the confirmed title.
    else:  # The quote is not confirmed.
        title = "Invoice quote:"  # Use the quote title.

    lines = [title]  # Start with the invoice title.

    for item in quote["items"]:  # Format each invoice item.
        lines.append(  # Add the item text.
            f"- {item['product_name']}: "  # Show the product name.
            f"{item['quantity_kg']} kg x "  # Show the quantity.
            f"{item['price_per_kg']} {quote['currency']}/kg "  # Show the price per kg.
            f"= {item['subtotal']} {quote['currency']}"  # Show the subtotal.
        )  # Finish the item text.

    lines.append(f"\nTotal: {quote['total']} {quote['currency']}")  # Add the invoice total.

    if confirmed:  # Choose the confirmation message.
        lines.append("Order confirmed. Inventory has been updated.")  # Report successful confirmation.
    else:  # Choose the pending-order message.
        lines.append(  # Add instructions for the user.
            "Stock has not been reserved or reduced.\n"  # Explain the stock status.
            "Type 'confirm order' to complete this order, "  # Explain how to confirm.
            "or 'cancel order' to discard it."  # Explain how to cancel.
        )  # Finish the instructions.

    return "\n".join(lines)  # Join the lines into one string.
