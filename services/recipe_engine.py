from services.product_catalog import find_product


def calculate_recipe_cost(recipe):
    total = 0

    for ingredient in recipe:
        product = find_product(ingredient["product"])

        if not product:
            continue

        total += (
            ingredient["amount"]
            * product["price_per_unit"]
        )

    return round(total, 2)