from decimal import Decimal, ROUND_HALF_UP  # Use decimals and half-up rounding.


def calculate(validated_items, currency):  # Calculate the invoice.
    cent = Decimal("0.01")  # Set two-decimal precision.
    total = Decimal("0")  # Start the total at zero.
    lines = []  # Store invoice items.

    for item in validated_items:  # Process each validated item.
        product = item["product"]  # Get the product record.
        quantity = item["quantity"]  # Get the requested quantity.
        price = Decimal(str(product["price_per_kg"]))  # Convert price to Decimal.

        subtotal = price * quantity  # Calculate the item's cost.
        subtotal = subtotal.quantize(cent, rounding=ROUND_HALF_UP)  # Round to two decimals.

        total = total + subtotal  # Add the subtotal to the total.

        lines.append({  # Add an invoice item.
            "product_name": product["name"],  # Store the product name.
            "quantity_kg": str(quantity),  # Store quantity as text.
            "price_per_kg": str(price),  # Store price as text.
            "subtotal": str(subtotal),  # Store subtotal as text.
        })  # Finish adding the item.

    return {  # Return the complete invoice.
        "currency": currency,  # Store the currency.
        "items": lines,  # Store all invoice items.
        "total": str(total.quantize(cent)),  # Store the rounded total as text.
    }  # Finish the invoice.
