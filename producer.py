"""Gửi CDR giả vào mblife.pbx.cdr.v1. Dùng: python producer.py --count 200"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

from confluent_kafka import Producer
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOPIC = "mblife.pbx.cdr.v1"
VN = timezone(timedelta(hours=7))
RUN_ID = time.time_ns() // 1000

parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=5)
args = parser.parse_args()

producer = Producer({
    "bootstrap.servers": f"{os.environ['VM_IP']}:9092",
    "acks": "all",
    "enable.idempotence": True,
    "compression.type": "zstd",
})
sent = {"ok": 0, "failed": 0}


def on_delivery(err, msg):
    if err:
        sent["failed"] += 1
        print(f"FAILED key={msg.key().decode()} err={err}")
    else:
        sent["ok"] += 1
        if args.count <= 10:
            print(f"OK key={msg.key().decode()} partition={msg.partition()} offset={msg.offset()}")


def make_cdr(i):
    end = datetime.now(VN).replace(microsecond=0)
    billsec = random.randint(0, 600)
    answered = billsec > 0
    start = end - timedelta(seconds=billsec + 4)
    linkedid = f"{RUN_ID}.{i}"
    return {
        "linkedid": linkedid,
        "uniqueid": linkedid,
        "direction": random.choice(["inbound", "outbound"]),
        "src": f"09{random.randint(10_000_000, 99_999_999)}",
        "dst": random.choice(["1001", "1002"]),
        "start": start.isoformat(),
        "answer": (start + timedelta(seconds=4)).isoformat() if answered else None,
        "end": end.isoformat(),
        "duration": billsec + 4,
        "billsec": billsec,
        "disposition": "ANSWERED" if answered else "NO ANSWER",
        "recording_url": None,
    }


for i in range(args.count):
    cdr = make_cdr(i)
    producer.produce(TOPIC, key=cdr["linkedid"], value=json.dumps(cdr).encode(), on_delivery=on_delivery)
    producer.poll(0)

producer.flush(15)
print(f"gửi thành công {sent['ok']}, thất bại {sent['failed']}")
