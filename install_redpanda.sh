#!/usr/bin/env bash
# Cài Redpanda native (apt + systemd) cho một node lab. Chạy lại nhiều lần không hỏng.
# Dùng: ssh root@<VM_IP> "bash -s -- <VM_IP>" < install_redpanda.sh
set -euo pipefail
VM_IP="${1:?thiếu IP: bash install_redpanda.sh <VM_IP>}"

if ! command -v rpk >/dev/null; then
  curl -1sLf 'https://linux.pkg.redpanda.com/setup-redpanda.deb.sh' | bash
  apt-get install -y redpanda
fi

rpk redpanda config bootstrap --self "$VM_IP" --advertised-kafka "$VM_IP" --ips "$VM_IP"
rpk redpanda config set redpanda.empty_seed_starts_cluster false
rpk redpanda config set rpk.additional_start_flags '["--memory=2G"]'

if ufw status | grep -q 'Status: active'; then
  ufw allow 9092/tcp
fi

systemctl enable redpanda
systemctl restart redpanda

for _ in $(seq 1 30); do
  rpk cluster health 2>/dev/null | grep -q 'Healthy:.*true' && break
  sleep 2
done
rpk cluster info
