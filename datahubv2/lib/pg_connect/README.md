# PostgreSQL Connection Library

Library สำหรับ connect PostgreSQL และ logging ข้อมูลโดยใช้ config จาก PG Logs doctype

## Setup

### 1. Install Dependencies

```bash
pip install psycopg2-binary
```

### 2. Configure PG Logs DocType

เข้าไปที่ **PG Logs** doctype ใน Frappe และกรอกข้อมูล:

- **Host**: PostgreSQL server host
- **Port**: PostgreSQL port (default: 5432)
- **DB Name**: Database name
- **User Name**: Database username
- **Password**: Database password

## Usage

### Quick Start

```python
from datahubv2.lib.pg_connect import log_to_postgres, log_before_after_to_postgres

# Simple logging
success = log_to_postgres(
    ref_id="98765",
    ref_module="order", 
    json_data={"status": "completed", "amount": 1500}
)

# Before/After logging
success = log_before_after_to_postgres(
    ref_id="98765",
    ref_module="order",
    before_data={"status": "pending", "amount": 1500},
    after_data={"status": "paid", "amount": 1500}
)
```

### Using Logger Class

```python
from datahubv2.lib.pg_connect import PGLogger

logger = PGLogger()

# Insert log
logger.insert_log(
    ref_id="12345",
    ref_module="customer",
    json_data={
        "action": "profile_update",
        "changes": {"email": "new@example.com"}
    }
)

# Retrieve logs
logs = logger.get_logs(ref_id="12345", limit=10)
```

### Using Client Directly

```python
from datahubv2.lib.pg_connect import PGClient

client = PGClient()

# Custom query
with client.get_cursor() as (cursor, conn):
    cursor.execute("SELECT * FROM my_data_log WHERE ref_id = %s", ("12345",))
    results = cursor.fetchall()
    conn.commit()
```

## Database Schema

Library จะสร้างตาราง `my_data_log` อัตโนมัติ:

```sql
CREATE TABLE IF NOT EXISTS my_data_log (
    id SERIAL PRIMARY KEY,
    ref_id VARCHAR(255) NOT NULL,
    ref_module VARCHAR(255) NOT NULL,
    json_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Reference

### PGClient

- `get_connection()`: Context manager สำหรับ PostgreSQL connection
- `get_cursor()`: Context manager สำหรับ database cursor

### PGLogger

- `insert_log(ref_id, ref_module, json_data)`: Insert log entry
- `insert_log_with_before_after(ref_id, ref_module, before_data, after_data)`: Insert before/after log
- `get_logs(ref_id, ref_module, limit, offset)`: Retrieve logs
- `create_log_table_if_not_exists()`: Create log table

### Convenience Functions

- `log_to_postgres(ref_id, ref_module, json_data)`: Quick logging function
- `log_before_after_to_postgres(ref_id, ref_module, before_data, after_data)`: Quick before/after logging
- `get_pg_client()`: Get PGClient instance
- `get_pg_logger()`: Get PGLogger instance

## Error Handling

Library จะ log errors ไปยัง Frappe Error Log อัตโนมัติ และ return `False` เมื่อเกิดข้อผิดพลาด

## Examples

ดูไฟล์ `example_usage.py` สำหรับตัวอย่างการใช้งานแบบละเอียด