"""Đọc mblife.pbx.cdr.v1 và lưu vào SQLite cdr.db, idempotent theo linkedid."""

import json
import os
import signal
import socket
import sqlite3
import sys

from confluent_kafka import Consumer
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOPIC = "mblife.pbx.cdr.v1"
GROUP = "cdr-backend-writer"
NAME = f"{socket.gethostname()}-{os.getpid()}"

db = sqlite3.connect("cdr.db")
db.execute("""
    CREATE TABLE IF NOT EXISTS cdr (
        linkedid TEXT PRIMARY KEY,
        src TEXT, dst TEXT, start TEXT, end TEXT,
        billsec INTEGER, disposition TEXT,
        kafka_partition INTEGER, kafka_offset INTEGER
    )
""")

consumer = Consumer({
    "bootstrap.servers": f"{os.environ['VM_IP']}:9092",
    "group.id": GROUP,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})

running = True


def stop(*_):
    global running
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def on_assign(_, partitions):
    print(f"[{NAME}] được giao partition {sorted(p.partition for p in partitions)}")


def save(cdr, msg):
    db.execute(
        """INSERT INTO cdr VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(linkedid) DO UPDATE SET
             billsec = excluded.billsec, disposition = excluded.disposition,
             kafka_partition = excluded.kafka_partition, kafka_offset = excluded.kafka_offset""",
        (cdr["linkedid"], cdr["src"], cdr["dst"], cdr["start"], cdr["end"],
         cdr["billsec"], cdr["disposition"], msg.partition(), msg.offset()),
    )


consumer.subscribe([TOPIC], on_assign=on_assign)
processed = 0
try:
    while running:
        batch = consumer.consume(num_messages=100, timeout=1.0)
        if not batch:
            continue
        for msg in batch:
            if msg.error():
                print(f"error: {msg.error()}")
                continue
            try:
                save(json.loads(msg.value()), msg)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"bỏ qua message hỏng partition={msg.partition()} offset={msg.offset()}: {e}")
        db.commit()
        consumer.commit(asynchronous=False)
        processed += len(batch)
        print(f"[{NAME}] đã xử lý {processed}")
finally:
    consumer.close()
    total = db.execute("SELECT COUNT(*) FROM cdr").fetchone()[0]
    print(f"[{NAME}] xử lý {processed} message lần này; bảng cdr có {total} dòng")
