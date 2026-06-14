import os
import time
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID = os.environ["THREADS_USER_ID"]


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_approved_product():
    url = f"{SUPABASE_URL}/rest/v1/products"
    params = {
        "status": "eq.approved",
        "select": "*",
        "limit": "1",
        "order": "approved_at.asc",
    }
    r = requests.get(url, headers=supabase_headers(), params=params, timeout=20)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def get_recent_posts():
    url = f"{SUPABASE_URL}/rest/v1/posts"
    params = {
        "select": "post_text",
        "order": "posted_at.desc",
        "limit": "30",
    }
    r = requests.get(url, headers=supabase_headers(), params=params, timeout=20)
    r.raise_for_status()
    return [x["post_text"] for x in r.json()]


def generate_text(product, recent_posts):
    recent_text = "\n".join(recent_posts)

    prompt = f"""
あなたはThreads向けに、生活雑貨を見つけたときの自然な短文を作る編集者です。

以下は過去の投稿です。

同じ話題の切り口
同じ感想
同じ書き出し
同じ語尾
同じ絵文字

を避けてください。

{recent_text}

今回の商品情報:
商品名: {product["item_name"]}
価格: {product["price"]}円
レビュー: {product["review_average"]}

作成条件:
- 60〜80文字
- 発見メモ風
- 売り込み感を出さない
- 商品名は使わない
- 商品価格は使わない
- ブランド名は必要な場合のみ使用可
- 画像を見たくなる一言にする
- 商品説明をしすぎない
- レビュー数値や価格は書かない
- 「おすすめ」「買うべき」「ゲット」「革命」「高評価」「楽天SS」は禁止
- PR表記やURLは入れない
- 出力は本文のみ
- 絵文字を文末に必ず1〜2個付ける
- 同じ絵文字を連続使用しない
- 「〜気がする」「〜かも」のような自然な独り言調を優先
- 断定表現を避ける
- 毎回違う切り口で書く

出力例:

こういう発想のものを見ると、
まだ知らない便利グッズって結構あるんだなと思う 👀✨

こういう地味な工夫、
意外と毎日の快適さに効きそう ☺️🪄

ぱっと見はシンプルだけど、
気になって何度も見てしまった 🌿👀

トーン:
「こんなのあるんだ」
「地味だけど気になる」
「こういう発想好き」
「生活の小さな不便を拾ってる感じ」
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()

    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def get_selected_image_urls(product):
    image_urls = product.get("image_urls") or []
    selected = product.get("selected_images") or []

    if not image_urls:
        return []

    if not selected:
        selected = [1, 2, 3]

    urls = []

    for index in selected:
        try:
            i = int(index) - 1
        except Exception:
            continue

        if 0 <= i < len(image_urls):
            urls.append(image_urls[i])

    return urls[:10]


def create_image_container(image_url):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    
    print("IMAGE URL:", image_url)
    
    payload = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "is_carousel_item": "true",
    }

    r = requests.post(
        url,
        params={"access_token": THREADS_ACCESS_TOKEN},
        data=payload,
        timeout=30,
    )

    print("IMAGE CONTAINER:", r.status_code, r.text)
    r.raise_for_status()

    return r.json()["id"]


def create_carousel_container(text, image_container_ids):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(image_container_ids),
        "text": text,
    }

    r = requests.post(
        url,
        params={"access_token": THREADS_ACCESS_TOKEN},
        data=payload,
        timeout=30,
    )

    print("CAROUSEL CONTAINER:", r.status_code, r.text)
    r.raise_for_status()

    return r.json()["id"]


def create_single_image_container(text, image_url):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    payload = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": text,
    }

    r = requests.post(
        url,
        params={"access_token": THREADS_ACCESS_TOKEN},
        data=payload,
        timeout=30,
    )

    print("SINGLE IMAGE CONTAINER:", r.status_code, r.text)
    r.raise_for_status()

    return r.json()["id"]


def publish_container(creation_id):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"

    payload = {
        "creation_id": creation_id,
    }

    r = requests.post(
        url,
        params={"access_token": THREADS_ACCESS_TOKEN},
        data=payload,
        timeout=30,
    )

    print("PUBLISH:", r.status_code, r.text)
    r.raise_for_status()

    return r.json()["id"]


def reply_with_affiliate(parent_post_id, affiliate_url):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"

    text = f"{affiliate_url} pr"

    payload = {
        "media_type": "TEXT",
        "text": text,
        "reply_to_id": parent_post_id,
    }

    create_res = requests.post(
        url,
        params={"access_token": THREADS_ACCESS_TOKEN},
        data=payload,
        timeout=30,
    )

    print("REPLY CONTAINER:", create_res.status_code, create_res.text)
    create_res.raise_for_status()

    creation_id = create_res.json()["id"]

    time.sleep(3)

    return publish_container(creation_id)


def update_product_posted(item_code, threads_post_id):
    url = f"{SUPABASE_URL}/rest/v1/products"

    params = {
        "item_code": f"eq.{item_code}",
    }

    payload = {
        "status": "posted",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "threads_post_id": threads_post_id,
    }

    r = requests.patch(
        url,
        headers=supabase_headers(),
        params=params,
        json=payload,
        timeout=20,
    )

    r.raise_for_status()


def save_post_history(product, post_text, threads_post_id, reply_post_id):
    url = f"{SUPABASE_URL}/rest/v1/posts"

    payload = {
        "item_code": product["item_code"],
        "post_text": post_text,
        "tone_type": "discovery",
        "emoji_used": "",
        "threads_post_id": threads_post_id,
        "reply_post_id": reply_post_id,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }

    r = requests.post(
        url,
        headers=supabase_headers(),
        json=payload,
        timeout=20,
    )

    r.raise_for_status()


def main():
    product = get_approved_product()

    if not product:
        print("No approved products")
        return

    recent_posts = get_recent_posts()
    post_text = generate_text(product, recent_posts)

    print("POST TEXT:")
    print(post_text)

    image_urls = get_selected_image_urls(product)

    if not image_urls:
        raise Exception("No image URLs found")

    if len(image_urls) == 1:
        creation_id = create_single_image_container(post_text, image_urls[0])
    else:
        child_ids = []

        for image_url in image_urls:
    try:
        child_id = create_image_container(image_url)
        child_ids.append(child_id)
        time.sleep(2)
    except Exception as e:
        print("SKIP IMAGE:", image_url)
        print("SKIP REASON:", e)
        continue

if not child_ids:
    raise Exception("All image containers failed")

        creation_id = create_carousel_container(post_text, child_ids)

    time.sleep(5)

    threads_post_id = publish_container(creation_id)

    time.sleep(5)

    reply_post_id = reply_with_affiliate(
        threads_post_id,
        product["affiliate_url"],
    )

    update_product_posted(
        product["item_code"],
        threads_post_id,
    )

    save_post_history(
        product,
        post_text,
        threads_post_id,
        reply_post_id,
    )

    print("DONE")
    print("THREADS_POST_ID:", threads_post_id)
    print("REPLY_POST_ID:", reply_post_id)


if __name__ == "__main__":
    main()
