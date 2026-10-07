"""Xoá VM, firewall và SSH key của lab (chỉ những thứ mang tên LAB_NAME)."""

import sys
import time

from vultr_common import NAME, call, find

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    inst = find("/instances", "instances", "label", NAME)
    group = find("/firewalls", "firewall_groups", "description", NAME)
    key = find("/ssh-keys", "ssh_keys", "name", NAME)

    targets = [
        ("instance", inst and f"{inst['id']} ({inst['main_ip']})"),
        ("firewall", group and group["id"]),
        ("ssh key", key and key["id"]),
    ]
    found = [(kind, desc) for kind, desc in targets if desc]
    if not found:
        print(f"Không còn tài nguyên nào tên {NAME}.")
        return
    for kind, desc in found:
        print(f"sẽ xoá {kind:9} {desc}")

    if "--yes" not in sys.argv and input(f"Gõ '{NAME}' để xác nhận: ").strip() != NAME:
        sys.exit("Huỷ.")

    if inst:
        call("DELETE", f"/instances/{inst['id']}")
        print("đã xoá instance")
    if group:
        for _ in range(12):
            if not find("/instances", "instances", "label", NAME):
                break
            time.sleep(5)
        call("DELETE", f"/firewalls/{group['id']}")
        print("đã xoá firewall")
    if key:
        call("DELETE", f"/ssh-keys/{key['id']}")
        print("đã xoá ssh key")


if __name__ == "__main__":
    main()
