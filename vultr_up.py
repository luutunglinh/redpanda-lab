"""Tạo SSH key, firewall và VM Ubuntu 24.04 cho lab. Chạy lại nhiều lần không tạo trùng."""

import time
from pathlib import Path

import requests
from dotenv import set_key

from vultr_common import ENV_FILE, NAME, call, find

REGION = "sgp"
PLAN = "vc2-2c-4gb"
OS_ID = 2284  # Ubuntu 24.04 LTS x64 — xác nhận bằng vultr_explore.py
PUBKEY = Path("~/.ssh/id_ed25519.pub").expanduser()
PORTS = ("22", "9092")


def ensure_ssh_key():
    key = find("/ssh-keys", "ssh_keys", "name", NAME)
    if key:
        print(f"ssh key   {NAME} đã có")
        return key["id"]
    if not PUBKEY.is_file():
        raise SystemExit(f"Không tìm thấy {PUBKEY} — chạy: ssh-keygen -t ed25519")
    key = call("POST", "/ssh-keys", json={"name": NAME, "ssh_key": PUBKEY.read_text().strip()})["ssh_key"]
    print(f"ssh key   {NAME} vừa tạo")
    return key["id"]


def ensure_firewall(my_ip):
    group = find("/firewalls", "firewall_groups", "description", NAME)
    if group:
        group_id = group["id"]
        print(f"firewall  {NAME} đã có")
    else:
        group_id = call("POST", "/firewalls", json={"description": NAME})["firewall_group"]["id"]
        print(f"firewall  {NAME} vừa tạo")

    rules = call("GET", f"/firewalls/{group_id}/rules")["firewall_rules"]
    existing = {(r["port"], r["subnet"]) for r in rules}
    for port in PORTS:
        if (port, my_ip) not in existing:
            call(
                "POST",
                f"/firewalls/{group_id}/rules",
                json={
                    "ip_type": "v4",
                    "protocol": "tcp",
                    "port": port,
                    "subnet": my_ip,
                    "subnet_size": 32,
                    "notes": NAME,
                },
            )
            print(f"firewall  mở tcp/{port} cho {my_ip}/32")
    return group_id


def ensure_instance(ssh_key_id, firewall_id):
    inst = find("/instances", "instances", "label", NAME)
    if inst:
        print(f"instance  {NAME} đã có")
    else:
        inst = call(
            "POST",
            "/instances",
            json={
                "region": REGION,
                "plan": PLAN,
                "os_id": OS_ID,
                "label": NAME,
                "hostname": NAME,
                "tags": ["lab"],
                "sshkey_id": [ssh_key_id],
                "firewall_group_id": firewall_id,
                "backups": "disabled",
            },
        )["instance"]
        print(f"instance  {NAME} vừa tạo, chờ khởi động...")

    while True:
        inst = call("GET", f"/instances/{inst['id']}")["instance"]
        state = (inst["status"], inst["power_status"], inst["server_status"])
        print(f"          status={state[0]} power={state[1]} server={state[2]} ip={inst['main_ip']}")
        if state == ("active", "running", "ok"):
            return inst
        time.sleep(10)


def main():
    my_ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
    print(f"IP của bạn: {my_ip}")
    inst = ensure_instance(ensure_ssh_key(), ensure_firewall(my_ip))
    set_key(str(ENV_FILE), "VM_IP", inst["main_ip"])
    print(f"\nXong. VM_IP={inst['main_ip']} đã ghi vào .env")
    print(f"Thử: ssh root@{inst['main_ip']} hostname")


if __name__ == "__main__":
    main()
