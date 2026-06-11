import os
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def count_approved():

    url = f"{SUPABASE_URL}/rest/v1/products"

    params = {
        "status": "eq.approved",
        "select": "id",
    }

    r = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=20,
    )

    r.raise_for_status()

    return len(r.json())


def send_discord(message):

    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "content": message
    }

    r = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20,
    )

    r.raise_for_status()


def main():

    approved_count = count_approved()

    print("APPROVED:", approved_count)

    if approved_count <= 5:

        send_discord(
            f"⚠️ approved商品が残り{approved_count}件です"
        )

        print("NOTIFIED")


if __name__ == "__main__":
    main()
