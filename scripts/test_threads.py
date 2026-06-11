import os
import requests

TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
USER_ID = os.environ["THREADS_USER_ID"]

# 1. 投稿コンテナ作成
create_url = f"https://graph.threads.net/v1.0/{USER_ID}/threads"

create_payload = {
    "media_type": "TEXT",
    "text": "🚀"
}

create_res = requests.post(
    create_url,
    params={"access_token": TOKEN},
    data=create_payload,
)

print("CREATE STATUS:", create_res.status_code)
print("CREATE BODY:", create_res.text)
create_res.raise_for_status()

creation_id = create_res.json()["id"]

# 2. 公開
publish_url = f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish"

publish_payload = {
    "creation_id": creation_id
}

publish_res = requests.post(
    publish_url,
    params={"access_token": TOKEN},
    data=publish_payload,
)

print("PUBLISH STATUS:", publish_res.status_code)
print("PUBLISH BODY:", publish_res.text)
publish_res.raise_for_status()
