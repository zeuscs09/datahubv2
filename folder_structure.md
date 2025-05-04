# DataHub Folder Structure

```
datahubv2/
├── datahubv2/
│   ├── __init__.py
│   ├── config.py                 # Configuration settings
│   ├── core/
│   │   ├── __init__.py
│   │   ├── validator.py          # Data validation classes
│   │   ├── processor.py          # Data processing classes
│   │   └── transformer.py        # Data transformation classes
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── inbound/
│   │   │   │   ├── __init__.py
│   │   │   │   └── profile.py   # Profile webhook endpoint
│   │   │   └── outbound/
│   │   │       ├── __init__.py
│   │   │       └── webhook.py    # Outbound webhook dispatch
│   │   └── v2/
│   ├── doctype/
│   │   ├── etl_main_profile/
│   │   │   ├── __init__.py
│   │   │   ├── etl_main_profile.json
│   │   │   ├── etl_main_profile.py
│   │   │   └── etl_main_profile.js
│   │   ├── etl_child/
│   │   │   ├── __init__.py
│   │   │   ├── etl_child.json
│   │   │   ├── etl_child.py
│   │   │   └── etl_child.js
│   │   ├── etl_campaign/
│   │   │   ├── __init__.py
│   │   │   ├── etl_campaign.json
│   │   │   ├── etl_campaign.py
│   │   │   └── etl_campaign.js
│   │   ├── etl_consent/
│   │   │   ├── __init__.py
│   │   │   ├── etl_consent.json
│   │   │   ├── etl_consent.py
│   │   │   └── etl_consent.js
│   │   ├── etl_sync_log/
│   │   │   ├── __init__.py
│   │   │   ├── etl_sync_log.json
│   │   │   ├── etl_sync_log.py
│   │   │   └── etl_sync_log.js
│   │   ├── dh_webhook_inbound/
│   │   │   ├── __init__.py
│   │   │   ├── dh_webhook_inbound.json
│   │   │   ├── dh_webhook_inbound.py
│   │   │   └── dh_webhook_inbound.js
│   │   ├── dh_webhook_outbound/
│   │   │   ├── __init__.py
│   │   │   ├── dh_webhook_outbound.json
│   │   │   ├── dh_webhook_outbound.py
│   │   │   └── dh_webhook_outbound.js
│   │   ├── data_validation_rules/
│   │   │   ├── __init__.py
│   │   │   ├── data_validation_rules.json
│   │   │   ├── data_validation_rules.py
│   │   │   └── data_validation_rules.js
│   │   └── data_mapping_rules/
│   │       ├── __init__.py
│   │       ├── data_mapping_rules.json
│   │       ├── data_mapping_rules.py
│   │       └── data_mapping_rules.js
│   ├── ic360/
│   │   ├── __init__.py
│   │   ├── connection.py         # PostgreSQL connection
│   │   ├── queries.py           # SQL queries
│   │   └── sync.py              # Sync functions
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── date.py              # Date utilities
│   │   ├── json.py              # JSON utilities
│   │   └── security.py          # Security utilities
│   └── tests/
│       ├── __init__.py
│       ├── test_validator.py
│       ├── test_processor.py
│       ├── test_transformer.py
│       ├── test_api.py
│       └── test_ic360.py
├── setup.py
├── requirements.txt
└── README.md
```

## โครงสร้างโฟลเดอร์หลัก

1. **Core Modules** (`core/`)
   - `validator.py`: ระบบตรวจสอบข้อมูล
   - `processor.py`: ระบบประมวลผลข้อมูล
   - `transformer.py`: ระบบแปลงข้อมูล

2. **API Layer**
   - `api/v1/inbound`: Webhook inbound endpoints
   - `api/v1/outbound`: Webhook outbound endpoints

3. **DocTypes**
   - `etl_main_profile`: ข้อมูลลูกค้าหลัก
   - `etl_child`: ข้อมูลเด็ก
   - `etl_campaign`: ข้อมูลแคมเปญ
   - `etl_consent`: ข้อมูลความยินยอม
   - `etl_sync_log`: บันทึกการ sync
   - `dh_webhook_inbound`: บันทึก webhook inbound
   - `dh_webhook_outbound`: บันทึก webhook outbound
   - `data_validation_rules`: กฎการตรวจสอบข้อมูล
   - `data_mapping_rules`: กฎการแมปข้อมูล

4. **IC360 Integration**
   - `connection.py`: การเชื่อมต่อ PostgreSQL
   - `queries.py`: SQL queries
   - `sync.py`: ฟังก์ชัน sync

5. **Utilities**
   - `date.py`: ฟังก์ชันเกี่ยวกับวันที่
   - `json.py`: ฟังก์ชันเกี่ยวกับ JSON
   - `security.py`: ฟังก์ชันเกี่ยวกับความปลอดภัย

6. **Tests**
   - Unit tests สำหรับทุกส่วนของระบบ

## การทำงานของระบบ

1. **Data Flow**
   - Webhook inbound -> DocType -> Transformer -> Processor -> DocType
   - DocType -> Transformer -> Webhook outbound
   - IC360 -> Transformer -> DocType
   - DocType -> Transformer -> IC360

2. **Validation Flow**
   - Input -> Validator -> Processor -> DocType
   - DocType -> Validator -> Output

3. **Sync Flow**
   - IC360 -> Queries -> Transformer -> DocType
   - DocType -> Transformer -> IC360
