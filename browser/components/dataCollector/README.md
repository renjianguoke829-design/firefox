# Data Collector

This service listens on `127.0.0.1:9999`, receives JSON lines from Firefox network interception points, and stores records in PostgreSQL.

Stored schema:
- `domain` (TEXT)
- `timestamp` (BIGINT, ms)
- `content` (TEXT)

## Run

```bash
python3 -m pip install -r browser/components/dataCollector/requirements.txt
DATABASE_URL=postgresql://postgres:password@localhost:5432/production \
  python3 browser/components/dataCollector/server.py
```
