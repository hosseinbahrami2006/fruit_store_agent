from decimal import Decimal, ROUND_HALF_UP


def calculate(validated_items, currency):
    """Calculate rounded subtotals and the total for a validated basket."""
    cent = Decimal("0.01")
    total = Decimal("0")
    lines = []

    for item in validated_items:
        product = item["product"]
        quantity = item["quantity"]
        price = Decimal(str(product["price_per_kg"]))

        subtotal = price * quantity
        subtotal = subtotal.quantize(cent, rounding=ROUND_HALF_UP)

        total = total + subtotal

        lines.append({
            "product_name": product["name"],
            "quantity_kg": str(quantity),
            "price_per_kg": str(price),
            "subtotal": str(subtotal),
        })

    return {
        "currency": currency,
        "items": lines,
        "total": str(total.quantize(cent)),
    }
