"""Đối chiếu tổng số message trong mblife.pbx.cdr.v1 với số dòng trong cdr.db."""

import os
import sqlite3
import sys

from confluent_kafka import Consumer, TopicPartition
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOPIC = "mblife.pbx.cdr.v1"

consumer = Consumer({
    "bootstrap.servers": f"{os.environ['VM_IP']}:9092",
    "group.id": "check-readonly",
    "enable.auto.commit": False,
})
partitions = consumer.list_topics(TOPIC, timeout=10).topics[TOPIC].partitions

total = 0
print("partition  high-watermark")
for p in sorted(partitions):
    _, high = consumer.get_watermark_offsets(TopicPartition(TOPIC, p), timeout=10)
    print(f"{p:>9}  {high:>14}")
    total += high
consumer.close()

rows = sqlite3.connect("cdr.db").execute("SELECT COUNT(*) FROM cdr").fetchone()[0]
print(f"\nKafka: {total} message, DB: {rows} dòng")
print("OK" if total == rows else f"LỆCH {total - rows}")
