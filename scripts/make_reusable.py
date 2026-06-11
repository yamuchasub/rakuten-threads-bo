import os
import requests
from datetime import datetime, timezone, timedelta

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]


def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def main():

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=60)
    ).isoformat()

    url = f"{SUPABASE_URL}/rest/v1/products"

    params = {
        "status": "eq.posted",
        "posted_at": f"lt.{cutoff}",
    }

    payload = {
        "status": "reusable"
    }

    r = requests.patch(
        url,
        headers=headers(),
        params=params,
        json=payload,
        timeout=30,
    )

    r.raise_for_status()

    print("Reusable update complete")


if __name__ == "__main__":
    main()
