#!/usr/bin/env python3
import json
import os
import socket
import threading
from datetime import datetime

import psycopg2

HOST = "127.0.0.1"
PORT = 9999
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/production")


def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS browser_collector_records (
                id BIGSERIAL PRIMARY KEY,
                domain TEXT NOT NULL,
                timestamp BIGINT NOT NULL,
                content TEXT NOT NULL
            )
            """
        )
    conn.commit()


def handle_client(client, conn):
    with client:
        data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        for line in data.splitlines():
            if not line:
                continue
            try:
                item = json.loads(line.decode("utf-8"))
                domain = item.get("domain") or ""
                ts = int(item.get("timestamp") or int(datetime.utcnow().timestamp() * 1000))
                content = item.get("content") or ""
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO browser_collector_records (domain, timestamp, content) VALUES (%s, %s, %s)",
                        (domain, ts, content),
                    )
                conn.commit()
            except Exception:
                conn.rollback()


def main():
    conn = psycopg2.connect(DATABASE_URL)
    init_db(conn)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(128)
    while True:
        client, _ = sock.accept()
        threading.Thread(target=handle_client, args=(client, conn), daemon=True).start()


if __name__ == "__main__":
    main()
