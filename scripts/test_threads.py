import os
import requests

TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
USER_ID = os.environ["THREADS_USER_ID"]

url = f"https://graph.threads.net/v1.0/{USER_ID}/threads"

payload = {
    "media_type": "TEXT",
    "text": "楽天Threads Bot テスト投稿🚀"
}

r = requests.post(
    url,
    params={
        "access_token": TOKEN
    },
    data=payload
)

print(r.status_code)
print(r.text)
