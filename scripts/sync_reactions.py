import os
import time
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_new_products():
    url = f"{SUPABASE_URL}/rest/v1/products"
    params = {
        "status": "eq.new",
        "discord_message_id": "not.is.null",
        "select": "item_code,discord_message_id",
        "limit": "20",
    }

    r = requests.get(url, headers=supabase_headers(), params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def has_thumbs_up(message_id):
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages/{message_id}"

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
    }

    time.sleep(1)

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    message = r.json()

    reactions = message.get("reactions", [])

    for reaction in reactions:
        emoji = reaction.get("emoji", {})

        if emoji.get("name") == "👍" and reaction.get("count", 0) >= 1:
            return True

    return False

def approve_product(item_code):
    url = f"{SUPABASE_URL}/rest/v1/products"

    params = {
        "item_code": f"eq.{item_code}",
    }

    payload = {
        "status": "approved",
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }

    r = requests.patch(
        url,
        headers=supabase_headers(),
        params=params,
        json=payload,
        timeout=20,
    )
    r.raise_for_status()


def main():
    products = get_new_products()
    approved = 0

    for product in products:
        item_code = product["item_code"]
        message_id = product["discord_message_id"]

        if has_thumbs_up(message_id):
            approve_product(item_code)
            approved += 1
            print(f"Approved: {item_code}")

    print(f"Approved {approved} products.")


if __name__ == "__main__":
    main()
