import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_FILE = Path(__file__).with_name(".env")
load_dotenv(ENV_FILE)

API = "https://api.vultr.com/v2"
NAME = os.environ.get("LAB_NAME", "lab-student")

session = requests.Session()
session.headers["Authorization"] = f"Bearer {os.environ['VULTR_API_KEY']}"


def call(method, path, **kwargs):
    r = session.request(method, API + path, timeout=30, **kwargs)
    if r.status_code >= 400:
        print(f"{method} {path} -> {r.status_code}")
        print(r.text)
        sys.exit(1)
    return r.json() if r.text else {}


def find(path, list_key, field, value):
    for item in call("GET", f"{path}?per_page=500")[list_key]:
        if item.get(field) == value:
            return item
    return None
