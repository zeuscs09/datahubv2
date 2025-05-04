**Data Hub System Flow Summary**

---

### 🏗️ System Architecture Summary (Functional View)

#### 🎯 Objective

สร้างระบบกลาง (Data Hub) สำหรับ:

* ดึงข้อมูลลูกค้าจาก iC360 (PostgreSQL)
* แปลงและเก็บเป็น Doctype ใน Frappe
* ส่งข้อมูลออกแบบ JSON ไปยังระบบภายนอก (เช่น ClickNext / SD)
* รับข้อมูลกลับจากภายนอกเพื่ออัปเดตข้อมูลใน Frappe และส่งกลับ iC360 ได้

---

### 🔄 ETL Flow Overview

#### 📥 1. iC360 → Data Hub (Extract + Load)

* Connect ผ่าน `psycopg2` → ดึงข้อมูลจาก PostgreSQL
* ตารางที่ใช้:

  * `ks_contact` → Main Profile
  * `nl_customer`, `nl_customer_moreinfo`, `nl_reason` → Child
  * `nl_primary_consent`, `nl_marketing_consent` → Consent
  * `nl_contact_campaign` → Campaign
* เก็บข้อมูลใน Doctype:

  * `ETL_MainProfile`, `ETL_Child`, `ETL_Consent`, `ETL_Campaign`

#### 📤 2. Data Hub → External System (Transform + Webhook)

* ใช้ `to_webhook()` สร้าง JSON
* แปลง lookup ด้วย `DH_Lookup_Map` (e.g., gender=9 → 'BB')
* ลบ field ที่ว่าง/null
* ส่ง POST ไปยัง URL จาก `DH_Setting`
* บันทึก log ใน `DH_Webhook_Log`

#### 📥 3. External → Data Hub (Receive + Normalize)

* รับ JSON ผ่าน API `/api/method/data_hub.receive_data`
* แปลงค่ากลับ (e.g., 'BB' → 9)
* ใช้ `from_webhook()` → update Doctype
* Match child โดย ±60 วันจากวันเกิด
* Log ว่ามีการ update / add child/campaign ใดบ้าง

#### 🔁 4. Data Hub → iC360 (Push Back)

* ใช้ `to_ic360_query()` สร้าง SQL update
* Run query ผ่าน `psycopg2` กลับไปยัง iC360 PostgreSQL

---

### ⚙️ Modules and Components

#### Doctypes

* `ETL_MainProfile`, `ETL_Child`, `ETL_Consent`, `ETL_Campaign`
* `DH_Webhook_Log`, `DH_Setting`, `Datahub_Sync`, `DH_Lookup_Map`

#### Python Modules

* `DBHelper`: สำหรับ PostgreSQL
* `Transformer`: from\_pg\_row(), to\_webhook(), from\_webhook(), to\_ic360\_query()
* `Webhook Dispatcher`: POST JSON
* `Inbound Processor`: รับ-แปลง-เก็บข้อมูลจากภายนอก

#### Background Jobs

* `sync_pending_profiles()`
* `sync_migration_profiles()`
* `dispatch_webhook()`
* `external_inbound_processor()`

---

### 🔎 Lookup Field Strategy

* ใช้ `DH_Lookup_Map` เพื่อจัดการการแปลงค่า เช่น:

  * iC360: gender = 9 → External: gender = "BB"
* รองรับทั้ง inbound/outbound

---

### 🧠 Best Practices

* ใช้ชื่อ field ตาม PostgreSQL เดิมใน Doctype (ไม่มี alias)
* ใช้ wrapper class แยก logic export/import เช่น `MainProfileTransformer`
* แยก raw query (extract) ออกจาก transformation (mapping)
* ทุกการส่ง/รับมีการ log
* ใช้ UUID จาก `nl_query_smartdata_project_uuid_migration` เป็น key กลาง

---

