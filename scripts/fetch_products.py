import os
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]

RAKUTEN_APP_ID = os.environ["RAKUTEN_APP_ID"]
RAKUTEN_AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "")

KEYWORDS = [
    "無印良品 公式",
    "tower 山崎実業",
    "キッチン 便利グッズ",
    "収納 便利グッズ",
    "防災 ライト",
]

MAX_POSTS = 30


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def product_exists(item_code):
    url = f"{SUPABASE_URL}/rest/v1/products"
    params = {
        "item_code": f"eq.{item_code}",
        "select": "item_code",
    }
    r = requests.get(url, headers=supabase_headers(), params=params, timeout=20)
    r.raise_for_status()
    return len(r.json()) > 0


def save_product(item, discord_message_id):
    url = f"{SUPABASE_URL}/rest/v1/products"

    image_url = ""
    if item.get("mediumImageUrls"):
        image_url = item["mediumImageUrls"][0]["imageUrl"].replace("?_ex=128x128", "")

    payload = {
        "item_code": item.get("itemCode"),
        "item_name": item.get("itemName"),
        "price": item.get("itemPrice"),
        "review_average": float(item.get("reviewAverage") or 0),
        "review_count": int(item.get("reviewCount") or 0),
        "image_url": image_url,
        "affiliate_url": item.get("affiliateUrl") or item.get("itemUrl"),
        "status": "new",
        "discord_message_id": discord_message_id,
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
    }

    r = requests.post(url, headers=supabase_headers(), json=payload, timeout=20)
    r.raise_for_status()


def fetch_rakuten(keyword, page=1):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": keyword,
        "hits": 30,
        "page": page,
        "sort": "-reviewAverage",
        "format": "json",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    return [x["Item"] for x in data.get("Items", [])]


def post_to_discord(item):
    image_url = ""
    if item.get("mediumImageUrls"):
        image_url = item["mediumImageUrls"][0]["imageUrl"].replace("?_ex=128x128", "")

    title = item.get("itemName", "")[:250]
    url = item.get("affiliateUrl") or item.get("itemUrl")

    embed = {
        "title": title,
        "url": url,
        "description": (
            f"価格：{item.get('itemPrice')}円\n"
            f"レビュー：{item.get('reviewAverage')} / {item.get('reviewCount')}件\n\n"
            f"👍で投稿候補に追加"
        ),
        "footer": {
            "text": item.get("itemCode", "")
        }
    }

    if image_url:
        embed["image"] = {"url": image_url}

    payload = {
        "embeds": [embed]
    }

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    api_url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    r = requests.post(api_url, headers=headers, json=payload, timeout=20)
    r.raise_for_status()

    return r.json()["id"]


def main():
    posted = 0

    for keyword in KEYWORDS:
        if posted >= MAX_POSTS:
            break

        items = fetch_rakuten(keyword)

        for item in items:
            if posted >= MAX_POSTS:
                break

            item_code = item.get("itemCode")
            if not item_code:
                continue

            if product_exists(item_code):
                continue

            review_average = float(item.get("reviewAverage") or 0)
            review_count = int(item.get("reviewCount") or 0)
            price = int(item.get("itemPrice") or 0)

            if review_average < 4.2:
                continue

            if review_count < 20:
                continue

            if price < 500 or price > 15000:
                continue

            message_id = post_to_discord(item)
            save_product(item, message_id)

            posted += 1

    print(f"Posted {posted} products to Discord.")


if __name__ == "__main__":
    main()
