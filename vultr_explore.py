"""Khám phá Vultr API — chỉ đọc, không tạo tài nguyên."""

import sys

from vultr_common import call

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REGION = "sgp"
PLAN = "vc2-2c-4gb"
OS_NAME = "Ubuntu 24.04 LTS x64"


def main() -> int:
    account = call("GET", "/account")["account"]
    balance = float(account.get("balance", 0))
    pending = float(account.get("pending_charges", 0))
    credit_left = -balance
    print(f"Số dư (raw balance): {balance}")
    print(f"Credit còn lại (ước tính): ${credit_left:.2f} (Vultr thường hiển thị balance âm khi còn credit)")
    print(f"Phí đang chờ tính: ${pending:.2f}")

    regions = {r["id"]: r for r in call("GET", "/regions")["regions"]}
    if REGION in regions:
        print(f'Region "{REGION}": có — {regions[REGION].get("city")}, {regions[REGION].get("country")}')
    else:
        print(f'Region "{REGION}": KHÔNG có')
        return 1

    plan_row = None
    for p in call("GET", "/plans?type=vc2")["plans"]:
        if p.get("id") == PLAN:
            plan_row = p
            break
    if not plan_row:
        print(f'Plan "{PLAN}": không tìm thấy')
        return 1

    monthly = plan_row.get("monthly_cost", plan_row.get("price"))
    ram_mb = plan_row.get("ram")
    vcpu = plan_row.get("vcpu_count", plan_row.get("vcpu"))
    in_sgp = REGION in plan_row.get("locations", [])
    print(f'Plan "{PLAN}": {vcpu} vCPU, {ram_mb} MB RAM, ${monthly}/tháng, có ở sgp: {in_sgp}')

    os_id = None
    for os_item in call("GET", "/os")["os"]:
        if os_item.get("name") == OS_NAME:
            os_id = os_item["id"]
            break
    if os_id is None:
        print(f'OS "{OS_NAME}": không tìm thấy')
        return 1
    print(f'OS "{OS_NAME}": os_id = {os_id}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
