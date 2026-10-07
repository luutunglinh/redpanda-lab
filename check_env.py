"""Kiểm tra file .env — không in toàn bộ API key."""

import os
import sys

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REQUIRED = ("VULTR_API_KEY", "LAB_NAME")


def main() -> int:
    if not load_dotenv():
        print("Không tìm thấy file .env — copy từ .env.example rồi điền giá trị.")
        return 1

    missing = [name for name in REQUIRED if not os.getenv(name, "").strip()]
    if missing:
        for name in missing:
            print(f"Thiếu hoặc rỗng: {name}")
        return 1

    lab_name = os.environ["LAB_NAME"].strip()
    key = os.environ["VULTR_API_KEY"].strip()
    print(f"LAB_NAME={lab_name}")
    print(f"VULTR_API_KEY (4 ký tự cuối)=...{key[-4:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
