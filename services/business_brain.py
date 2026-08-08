from datetime import datetime


def morning_brief():
    hour = datetime.now().hour

    if hour < 12:
        greeting = "Good morning ☀️"
    elif hour < 18:
        greeting = "Good afternoon 🌤️"
    else:
        greeting = "Good evening 🌙"

    return {
        "greeting": greeting,
        "title": "Welcome back to Barni",
        "items": [
            "No new invoices today.",
            "Waiting for new business documents.",
            "Business memory is ready to grow."
        ],
    }