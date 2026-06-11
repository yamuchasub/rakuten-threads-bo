import os
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def get_approved_product():
    url = f"{SUPABASE_URL}/rest/v1/products"

    params = {
        "status": "eq.approved",
        "select": "*",
        "limit": "1",
    }

    r = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=20,
    )

    r.raise_for_status()

    rows = r.json()

    if not rows:
        return None

    return rows[0]


def get_recent_posts():
    url = f"{SUPABASE_URL}/rest/v1/posts"

    params = {
        "select": "post_text",
        "order": "posted_at.desc",
        "limit": "30",
    }

    r = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=20,
    )

    r.raise_for_status()

    return [x["post_text"] for x in r.json()]


def generate_text(product, recent_posts):

    recent_text = "\n".join(recent_posts)

    prompt = f"""
以下は直近30件のThreads投稿です。

{recent_text}

同じ書き出し
同じ語尾
同じ絵文字
同じ構成

を避けてください。

商品名:
{product["item_name"]}

価格:
{product["price"]}円

レビュー:
{product["review_average"]}

60文字以内で作成してください。
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    r = requests.post(url, json=payload, timeout=60)

    r.raise_for_status()

    data = r.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


def main():

    product = get_approved_product()

    if not product:
        print("No approved products")
        return

    recent_posts = get_recent_posts()

    text = generate_text(
        product,
        recent_posts
    )

    print("=== GENERATED ===")
    print(text)


if __name__ == "__main__":
    main()
