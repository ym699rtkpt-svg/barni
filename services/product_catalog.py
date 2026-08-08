def get_products():
    """
    בעתיד יחזיר את כל המוצרים מהדאטהבייס.
    כרגע רק דוגמא.
    """

    return [
        
        {
            "name": "Mozzarella",
            "unit": "g",
            "price_per_unit": 0.045,
        },
        {
            "name": "Tomato",
            "unit": "g",
            "price_per_unit": 0.012,
        },
        {
            "name": "Burger Bun",
            "unit": "piece",
            "price_per_unit": 1.20,
        },
    ]
def find_product(name: str):
    """
    מחפש מוצר לפי שם.
    """

    search = name.lower().strip()

    for product in get_products():
        if product["name"].lower() == search:
            return product

    return None