# DataHub System Design

## 1. Overview
ระบบ Data Hub ทำหน้าที่เป็นตัวกลางในการแลกเปลี่ยนข้อมูลระหว่าง IC360 และระบบภายนอก โดยมีการจัดการข้อมูลลูกค้า ข้อมูลเด็ก ข้อมูลแคมเปญ และข้อมูลความยินยอม

## 2. Core Components

### 2.1 Data Models

#### 2.1.1 ETL Main Profile
- DocType: `ETL Main Profile`
- Fields:
  - Basic Info:
    - `contact_id`: รหัสประจำตัวโปรไฟล์ (IC360: ks_contact.contact_id)
    - `uid`: รหัสประจำตัวโปรไฟล์ (JSON: uid)
    - `first_name`: ชื่อ (IC360: ks_contact.first_name, JSON: firstname)
    - `last_name`: นามสกุล (IC360: ks_contact.last_name, JSON: lastname)
    - `gender`: เพศ (IC360: ks_contact.gender) , look up key "GENDER" 
    - `gender_sd`: เพศ (JSON: gender) , look up key "GENDER"
    - `birth_date`: วันเกิด (IC360: ks_contact.birth_date, JSON: mom_birthdate)

  - Contact Info:
    - `phone`: เบอร์โทรศัพท์ (IC360: ks_contact.phone, JSON: phonenumber)
    - `email`: อีเมล (IC360: ks_contact.email, JSON: email)
    - `line_mid`: Line ID (IC360: ks_contact.line_mid, JSON: line_mid)
  - Address Info:
    - `address`: ที่อยู่ (IC360: ks_contact_moreinfo.address, JSON: addressline1)
    - `state_code` : ชื่อจังหวัด (IC360: ks_contact_moreinfo.state_code)
    - `province_name`: ชื่อจังหวัด (JSON: region)
    - `city`: ชื่ออำเภอ (IC360: ks_contact_moreinfo.city)
    - `amphur_name`: ชื่ออำเภอ (JSON: city)
    - `sub_district`: ชื่อตำบล (IC360: ks_contact_moreinfo.sub_district)
    - `sub_district_name`: ชื่อตำบล (JSON: addressline2)
    - `postal_code`: รหัสไปรษณีย์ (IC360: ks_contact_moreinfo.postal_code, JSON: zip)


  - Additional Info:
    - `income`: รายได้ (IC360: ks_contact_moreinfo.income, JSON: income)
    - `contact_source`: แหล่งที่มาของการติดต่อ (IC360: ks_contact.contact_source, JSON: contact_source)
    - `brand`: แบรนด์ (IC360: ks_contact.brand, JSON: brand)
    - `status`: สถานะ (IC360: ks_contact.status, JSON: status)
    - `sourceid`: รหัสแหล่งที่มาของข้อมูล (IC360: ks_contact.sourceid)  look up key "DataSourceCode" 
    - `data_source_code`: รหัสแหล่งที่มาของข้อมูล (JSON: data_source_code) , look up key "DataSourceCode" 
    - `nestle_agent_referral_code`: รหัสอ้างอิงตัวแทน (IC360: ks_contact.nestle_agent_referral_code, JSON: nestle_agent_referral_code)
  - Marketing Consent Info:
    - `is_consented`: สถานะการยินยอมรับข้อมูลการตลาด (JSON: Is_MKT_Subscribed)
    - `marketing_subscribed_date`: วันที่ยินยอมรับข้อมูลการตลาด (JSON: MKT_Subscribed_Date)
    - `marketing_subscribed_version`: เวอร์ชันการยินยอมรับข้อมูลการตลาด (JSON: MKT_Subscribed_Version)
  - Child Info:
    - `gg_hospital`: ประเภทโรงพยาบาล (จากเด็กคนล่าสุด, JSON: gg_hospital) ข้อมูลลูกที่เกิดคนสุดค้าย
    - `gg_child_delivery_type`: ประเภทการคลอด (จากเด็กคนล่าสุด, JSON: gg_child_delivery_type) ข้อมูลลูกที่เกิดคนสุดค้าย
    - `gg_milk_currently_consuming`: สูตรนมที่ใช้ในปัจจุบัน (จากเด็กคนล่าสุด, JSON: gg_milk_currently_consuming) ข้อมูลลูกที่เกิดคนสุดค้าย
    - `child_birthdatereliability`: ความน่าเชื่อถือของวันเกิดเด็ก (จากเด็กคนล่าสุด,JSON: child_birthdatereliability) ข้อมูลลูกที่เกิดคนสุดค้าย key NL_MOTHERSTAGE
  - System Info:
    - `date_registration`: วันที่ลงทะเบียน (IC360: ks_contact.date_registration, JSON: date_registration)
    - `last_updated`: วันที่อัพเดตล่าสุด (IC360: ks_contact.last_updated, JSON: last_updated)

#### 2.1.2 ETL Child
- DocType: `ETL Child`
- Fields:
  - Basic Info:
    - `cusid`: รหัสประจำตัวเด็ก (IC360: nl_customer.cusid, JSON: child_id)
    - `motherid`: โปรไฟล์แม่ (IC360: nl_customer.motherid)
    - `fname`: ชื่อ (IC360: nl_customer.fname)
    - `lname`: นามสกุล (IC360: nl_customer.lname)
    - `gender`: เพศ (IC360: nl_customer.gender)
    - `birthdate`: วันเกิด (IC360: nl_customer.birthdate, JSON: child_birthdate)
    - `nname`: ชื่อเล่น (IC360: nl_customer.nname, JSON: child_firstname)
  - Child Details:
    - `child_type`: ประเภทเด็ก (IC360: nl_customer.child_type)
    - `child_status`: สถานะเด็ก (IC360: nl_customer.child_status)
    - `child_stage`: ระยะของเด็ก (IC360: nl_customer.child_stage)
    - `born_place_id`: ประเภทโรงพยาบาล (IC360: nl_customer_moreinfo.born_place_id)
    - `born_place_type`: ประเภทโรงพยาบาล (IC360: nl_customer_moreinfo.born_place_type) 
    - `gg_hospital`: ประเภทโรงพยาบาล (จากเด็กคนล่าสุด, JSON: gg_hospital)  look up key NL_ANC_PLACE
    - `birth_plan`: ประเภทการคลอด (IC360: nl_customer_moreinfo.birth_plan)
    - `gg_child_delivery_type`: ประเภทการคลอด (จากเด็กคนล่าสุด, JSON: gg_child_delivery_type) look up key NL_BIRTH_PLAN
    - `mother_prod_id`: ผลิตภัณฑ์เดิมของแม่ (IC360: nl_customer_moreinfo.mother_prod_id)
    - `current_mother_prod_id`: ผลิตภัณฑ์ปัจจุบันของแม่ (IC360: nl_customer_moreinfo.current_mother_prod_id)
    - `firstpro`: ผลิตภัณฑ์แรก (IC360: nl_customer.firstpro)
    - `firstformula`: สูตรนมแรก (IC360: nl_customer.firstformula)
    - `lastpro`: ผลิตภัณฑ์ล่าสุด (IC360: nl_customer.lastpro) lookup formula
    - `lastformula`: สูตรนมล่าสุด (IC360: nl_customer.lastformula) lookup formula
    - `gg_milk_currently_consuming`: สูตรนมที่ใช้ในปัจจุบัน (จากเด็กคนล่าสุด, JSON: gg_milk_currently_consuming) ข้อมูลลูกที่เกิดคนสุดค้าย look up formula
  - Additional Info:
    - `reasonid`: รหัสเหตุผล (IC360: nl_customer.reasonid)
    - `reason`: เหตุผล (IC360: nl_customer.reason, JSON: reason)
    - `pc_code`: รหัส PC (IC360: nl_customer_moreinfo.pc_code, JSON: pc_code)
    - `mother_stage`: ระยะของแม่ (IC360: nl_customer_moreinfo.mother_stage) look up key NL_MOTHERSTAGE
    - `child_birthdatereliability`: ความน่าเชื่อถือของวันเกิดเด็ก (จากเด็กคนล่าสุด,JSON: child_birthdatereliability) look up key 
     NL_MOTHERSTAGE
    - `remark`: หมายเหตุ (IC360: nl_customer.remark)
  - System Info:
    - `createid`: ผู้สร้าง (IC360: nl_customer.createid)
    - `createdate`: วันที่สร้าง (IC360: nl_customer.createdate)
    - `updateid`: ผู้แก้ไข (IC360: nl_customer.updateid)
    - `updatedate`: วันที่แก้ไข (IC360: nl_customer.updatedate)
    - `flag_complete`: สถานะความสมบูรณ์ (IC360: nl_customer.flag_complete)
    - `flag_active`: สถานะการใช้งาน (IC360: nl_customer.flag_active)
    - `receivedate`: วันที่รับข้อมูล (IC360: nl_customer.receivedate)
    - `signature`: ลายเซ็น (IC360: nl_customer.signature)

#### 2.1.3 ETL Campaign
- DocType: `ETL Campaign`
- Fields:
  - Basic Info:
    - `campaign_id`: รหัสแคมเปญ
    - `parent`: โปรไฟล์แม่ (IC360: nl_contact_campaign.contact_id)
  - Campaign Info:
    - `campaign_name`: ชื่อแคมเปญ (IC360: nl_contact_campaign.campaign_name)
    - `campaign_type`: ประเภทแคมเปญ (IC360: nl_contact_campaign.campaign_type)
    - `campaign_status`: สถานะแคมเปญ (IC360: nl_contact_campaign.campaign_status)
    - `campaign_start_date`: วันที่เริ่มแคมเปญ (IC360: nl_contact_campaign.campaign_start_date)
    - `campaign_end_date`: วันที่สิ้นสุดแคมเปญ (IC360: nl_contact_campaign.campaign_end_date)
  - Application Info:
    - `application_code`: รหัสแอปพลิเคชัน (IC360: nl_contact_campaign.application_code, JSON: applicationCode)
    - `internal_id`: รหัสภายใน (IC360: nl_contact_campaign.internal_id, JSON: internaIdentifier)
    - `internal_alternate_id`: รหัสภายในสำรอง (IC360: nl_contact_campaign.internal_alternate_id, JSON: internalAlternateIdentifier)
    - `create_date`: วันที่สร้าง (IC360: nl_contact_campaign.create_date, JSON: createDate)
    - `last_update_date`: วันที่อัพเดทล่าสุด (IC360: nl_contact_campaign.last_update_date, JSON: lastUpdateDate)
  - System Info:
    - `date_registration`: วันที่ลงทะเบียน
    - `last_updated`: วันที่อัพเดตล่าสุด

#### 2.1.4 ETL Consent
- DocType: `ETL Consent`
- Fields:
  - Basic Info:
    - `consent_id`: รหัสความยินยอม
    - `parent`: โปรไฟล์แม่ (IC360: nl_marketing_consent.contact_id / nl_primary_consent.contact_id)
  - Consent Info:
    - `consent_type`: ประเภทความยินยอม (PRIVACY/MARKETING)
    - `consent_status`: สถานะความยินยอม
    - `consent_date`: วันที่ให้ความยินยอม (IC360: nl_marketing_consent.consent_marketing_dt / nl_primary_consent.privacy_13y_dt, JSON: consent_date)
    - `consent_version`: เวอร์ชันความยินยอม (IC360: nl_marketing_consent.consent_version / nl_primary_consent.consent_version, JSON: consent_version)
    - `is_consented`: สถานะการยินยอม (Yes/No, JSON: Is_MKT_Subscribed)
    - `marketing_subscribed_date`: วันที่ยินยอมรับข้อมูลการตลาด (JSON: MKT_Subscribed_Date)
    - `marketing_subscribed_version`: เวอร์ชันการยินยอมรับข้อมูลการตลาด (JSON: MKT_Subscribed_Version)
  - Consent Details:
    - `consent_description`: รายละเอียดความยินยอม
    - `consent_notes`: หมายเหตุความยินยอม
  - System Info:
    - `date_registration`: วันที่ลงทะเบียน
    - `last_updated`: วันที่อัพเดตล่าสุด

#### 2.1.5 ETL Sync Log
- DocType: `ETL Sync Log`
- Fields:
  - `sync_id`: รหัสการ sync
  - `sync_type`: ประเภทการ sync (PENDING/MIGRATION)
  - `sync_date`: วันที่ sync
  - `status`: สถานะ
  - `total_records`: จำนวนรายการทั้งหมด
  - `processed_records`: จำนวนรายการที่ประมวลผลแล้ว
  - `raw_data`: ข้อมูลดิบ (JSON)
  - `error_log`: บันทึกข้อผิดพลาด

#### 2.1.6 DH Webhook Outbound
- DocType: `DH Webhook Outbound`
- Fields:
  - `outbound_id`: รหัส outbound (Auto)
  - `profile_id`: Link to ETL Main Profile
  - `sent_to`: ระบบปลายทาง (เช่น "CRM", "Marketing", "Analytics")
  - `webhook_url`: URL ปลายทาง
  - `payload`: ข้อมูลที่ส่ง (JSON)
  - `headers`: HTTP Headers (JSON)
  - `status`: สถานะ (Pending/Sent/Failed)
  - `response_code`: HTTP Response Code
  - `response_body`: Response จากปลายทาง (JSON)
  - `error_message`: ข้อความข้อผิดพลาด
  - `retry_count`: จำนวนครั้งที่ retry
  - `created_at`: เวลาที่สร้าง
  - `sent_at`: เวลาที่ส่ง
  - `completed_at`: เวลาที่เสร็จสิ้น



## 4. Database Queries

### 4.1 ETL Main Profile Queries
```sql
-- Main Profile Query
SELECT 
    c.contact_id,
    c.first_name,
    c.last_name,
    c.contact_no,
    c.is_active,
    c.gender,
    c.birth_date,
    c.contact_type,
    c.create_user_id,
    c.create_company_id,
    c.create_group_id,
    c.create_dt,
    c.last_upd_user_id,
    c.last_upd_company_id,
    c.last_upd_group_id,
    c.last_upd_dt,
    c.id_card_no,
    c.contact_source,
    COALESCE(NULLIF(CASE 
        WHEN c.income ~ '^[0-9]+\.?[0-9]*$' THEN c.income 
        ELSE '0' 
    END, ''), '0')::numeric as income,
    ca.addr_1,
    ca.sub_district,
    ma.district_name as sub_district_name,
    ca.city,
    ma.amphur_name,
    ca.state_code,
    ma.province_name,
    ma.zipcode postal_code,
    ca.country_code,
    cl.line_mid,
    ce.channel_info as email,
    cm.channel_info as mobile,
    nkc.sourceid,
    nkc.flag_complete,
    nkc.register_date,
    nkc.mother_stage,
    nkc.agent_referral_code,
    coalesce(uuid.uuid, '') as uid
FROM 
    ks_contact c
LEFT JOIN 
    ks_contact_addr_dtl ca ON c.contact_id = ca.contact_id 
    AND ca.address_type = 'HOME'
LEFT JOIN 
    ks_contact_channel_lineinfo cl ON c.contact_id = cl.contact_id
LEFT JOIN 
    ks_contact_channel_dtl ce ON c.contact_id = ce.contact_id 
    AND ce.channel_type = 'PE' AND ce.is_primary=1
LEFT JOIN 
    ks_contact_channel_dtl cm ON c.contact_id = cm.contact_id 
    AND cm.channel_type = 'M' AND cm.is_primary=1
LEFT JOIN (
    SELECT
        province_code,
        province_name,
        amphur_code,
        amphur_name,
        district_code,
        district_name,
        zipcode 
    FROM
        ks_province kp
) ma ON ca.sub_district = ma.district_code 
    AND ca.city = ma.amphur_code 
    AND ca.state_code = ma.province_code
LEFT JOIN 
    nl_ks_contact nkc ON c.contact_id = nkc.contact_id 
LEFT JOIN 
    nl_query_smartdata_project_uuid_migration uuid ON c.contact_id = uuid.contact_id
WHERE 
    c.contact_id = %s

-- Area Information Query
SELECT
    province_code,
    province_name,
    amphur_code,
    amphur_name,
    district_code,
    district_name,
    zipcode 
FROM
    ks_province
WHERE 
    province_name = %s
    AND amphur_name = %s
    AND district_name = %s
LIMIT 1
```

### 4.2 ETL Child Queries
```sql
-- Child Data Query
SELECT 
    c.cusid,
    c.motherid,
    c.fname,
    c.lname, 
    c.nname,
    c.gender,
    c.birthdate,
    c.reasonid,
    rs.reasonth reasonidtext,
    c.reason,
    c.remark,
    c.firstpro,
    c.firstformula,
    c.lastpro,
    c.lastformula,
    c.createid,
    c.createdate,
    c.updateid,
    c.updatedate,
    c.flag_complete,
    c.flag_active,
    c.receivedate,
    c.signature,
    m.born_place_id,
    m.born_place_type,
    m.birth_plan,
    m.mother_prod_id,
    m.current_mother_prod_id,
    m.pc_code,
    m.mother_stage
FROM nl_customer c
LEFT JOIN nl_customer_moreinfo m ON c.cusid = m.cusid 
LEFT JOIN nl_reason rs on c.reasonid =rs.reasonid 
WHERE c.motherid = %(contact_id)s
AND c.flag_active = '1'
```

### 4.3 ETL Campaign Queries
```sql
-- Campaign Data Query
SELECT 
    contact_id,
    application_code,
    internal_id,
    internal_alternate_id,
    create_dt,
    last_upd_dt
FROM nl_contact_campaign 
WHERE contact_id = %s
```

### 4.4 ETL Consent Queries
```sql
-- Privacy Consent Query
SELECT 
    contact_id,
    register_dt,
    channel,
    consent_privacy_13y,
    privacy_13y_dt,
    consent_version,
    create_dt,
    last_upd_dt
FROM nl_primary_consent 
WHERE contact_id = %s

-- Marketing Consent Query
SELECT 
    contact_id,
    channel,
    consent_marketing,
    consent_marketing_dt,
    consent_version,
    create_dt,
    last_upd_dt
FROM nl_marketing_consent 
WHERE contact_id = %s
```

### 4.5 Sync Queries
```sql
-- Pending Actions Query
SELECT
    nsdq.contact_id,
    nsdq.customer_id,
    nsdq.action_type,
    nsdq.ref_no,
    nsdq.action_dt,
    nsdq.status_id,
    ROW_NUMBER() OVER(
        PARTITION BY nsdq.contact_id 
        ORDER BY nsdq.action_dt DESC
    ) rw
FROM
    nl_smartdata_dataout_q nsdq
LEFT JOIN 
    datahub_sync ds ON ds.ref_no = nsdq.ref_no
WHERE
    ds.ref_no IS NULL

-- Migration Data Query
SELECT 
    contact_id,
    'Migrate-c' AS customer_id,
    'migrate-a' AS action_type,
    uuid AS ref_no,
    now() AT TIME ZONE 'Asia/Bangkok' AS action_dt,
    9 AS status_id,
    1 AS rw
FROM nl_query_smartdata_project_uuid_migration mg
LEFT JOIN datahub_sync ds ON ds.ref_no = mg.uuid
WHERE ds.ref_no IS NULL

-- Sync Record Query
INSERT INTO datahub_sync (ref_no, syncdate)
VALUES (%s, NOW())
ON CONFLICT (ref_no) 
DO UPDATE SET syncdate = NOW()
```

## 5. Field Mapping

### 5.1 ETL Main Profile Field Mapping

| Field Name | IC360 Field | JSON Field | Lookup Key | Description |
|------------|-------------|------------|------------|-------------|
| contact_id | ks_contact.contact_id | - | - | รหัสประจำตัวโปรไฟล์ |
| uid | - | uid | - | UUID ของโปรไฟล์ |
| first_name | ks_contact.first_name | firstname | - | ชื่อ |
| last_name | ks_contact.last_name | lastname | - | นามสกุล |
| gender | ks_contact.gender | - | GENDER | เพศ |
| gender_sd | - | gender | GENDER | เพศ |
| birth_date | ks_contact.birth_date | mom_birthdate | - | วันเกิด |
| phone | ks_contact.phone | phonenumber | - | เบอร์โทรศัพท์ |
| email | ks_contact.email | email | - | อีเมล |
| line_mid | ks_contact.line_mid | line_mid | - | Line ID |
| address | ks_contact_moreinfo.address | addressline1 | - | ที่อยู่ |
| state_code | ks_contact_moreinfo.state_code | - | - | รหัสจังหวัด |
| province_name | - | region | - | ชื่อจังหวัด |
| city | ks_contact_moreinfo.city | - | - | รหัสอำเภอ |
| amphur_name | - | city | - | ชื่ออำเภอ |
| sub_district | ks_contact_moreinfo.sub_district | - | - | รหัสตำบล |
| sub_district_name | - | addressline2 | - | ชื่อตำบล |
| postal_code | ks_contact_moreinfo.postal_code | zip | - | รหัสไปรษณีย์ |
| income | ks_contact_moreinfo.income | income | - | รายได้ |
| contact_source | ks_contact.contact_source | contact_source | - | แหล่งที่มาของการติดต่อ |
| brand | ks_contact.brand | brand | - | แบรนด์ |
| status | ks_contact.status | status | - | สถานะ |
| sourceid | ks_contact.sourceid | - | DataSourceCode| รหัสแหล่งที่มาของข้อมูล |
| data_source_code | - | data_source_code | DataSourceCode | รหัสแหล่งที่มาของข้อมูล |
| nestle_agent_referral_code | ks_contact.nestle_agent_referral_code | nestle_agent_referral_code | - | รหัสอ้างอิงตัวแทน |
| is_consented | - | Is_MKT_Subscribed | - | สถานะการยินยอมรับข้อมูลการตลาด |
| marketing_subscribed_date | - | MKT_Subscribed_Date | - | วันที่ยินยอมรับข้อมูลการตลาด |
| marketing_subscribed_version | - | MKT_Subscribed_Version | - | เวอร์ชันการยินยอมรับข้อมูลการตลาด |
| gg_hospital | - | gg_hospital | NL_ANC_PLACE | ประเภทโรงพยาบาล (จากเด็กคนล่าสุด) |
| gg_child_delivery_type | - | gg_child_delivery_type | NL_BIRTH_PLAN | ประเภทการคลอด (จากเด็กคนล่าสุด) |
| gg_milk_currently_consuming | - | gg_milk_currently_consuming | NL_FORMULA | สูตรนมที่ใช้ในปัจจุบัน (จากเด็กคนล่าสุด) |
| child_birthdatereliability | - | child_birthdatereliability | NL_MOTHERSTAGE | ความน่าเชื่อถือของวันเกิดเด็ก |
| date_registration | ks_contact.date_registration | date_registration | - | วันที่ลงทะเบียน |
| last_updated | ks_contact.last_updated | last_updated | - | วันที่อัพเดตล่าสุด |

### 5.2 ETL Child Field Mapping

| Field Name | IC360 Field | JSON Field | Lookup Key | Description |
|------------|-------------|------------|------------|-------------|
| cusid | nl_customer.cusid | child_id | - | รหัสประจำตัวเด็ก |
| motherid | nl_customer.motherid | - | - | โปรไฟล์แม่ |
| fname | nl_customer.fname | - | - | ชื่อ |
| lname | nl_customer.lname | - | - | นามสกุล |
| nname | nl_customer.nname |child_firstname | - | ชื่อเล่น |
| gender | nl_customer.gender | - | - | เพศ |
| birthdate | nl_customer.birthdate | child_birthdate | - | วันเกิด |
| child_type | nl_customer.child_type | - | - | ประเภทเด็ก |
| child_status | nl_customer.child_status | - | - | สถานะเด็ก |
| child_stage | nl_customer.child_stage | - | - | ระยะของเด็ก |
| born_place_id | nl_customer_moreinfo.born_place_id | - | - | ประเภทโรงพยาบาล |
| born_place_type | nl_customer_moreinfo.born_place_type | - | - | ประเภทโรงพยาบาล |
| gg_hospital | - | gg_hospital | NL_ANC_PLACE | ประเภทโรงพยาบาล (จากเด็กคนล่าสุด) |
| birth_plan | nl_customer_moreinfo.birth_plan | - | - | ประเภทการคลอด |
| gg_child_delivery_type | - | gg_child_delivery_type | NL_BIRTH_PLAN | ประเภทการคลอด (จากเด็กคนล่าสุด) |
| mother_prod_id | nl_customer_moreinfo.mother_prod_id | - | - | ผลิตภัณฑ์เดิมของแม่ |
| current_mother_prod_id | nl_customer_moreinfo.current_mother_prod_id | - | - | ผลิตภัณฑ์ปัจจุบันของแม่ |
| firstpro | nl_customer.firstpro | - | formula | ผลิตภัณฑ์แรก |
| firstformula | nl_customer.firstformula | - | formula | สูตรนมแรก |
| lastpro | nl_customer.lastpro | - | formula | ผลิตภัณฑ์ล่าสุด |
| lastformula | nl_customer.lastformula | - | formula | สูตรนมล่าสุด |
| gg_milk_currently_consuming | - | gg_milk_currently_consuming | NL_FORMULA | สูตรนมที่ใช้ในปัจจุบัน |
| reasonid | nl_customer.reasonid | - | - | รหัสเหตุผล |
| reason | nl_customer.reason | reason | - | เหตุผล |
| remark | nl_customer.remark | - | - | หมายเหตุ |
| pc_code | nl_customer_moreinfo.pc_code | pc_code | - | รหัส PC |
| mother_stage | nl_customer_moreinfo.mother_stage | - | NL_MOTHERSTAGE | ระยะของแม่ |
| child_birthdatereliability | - | child_birthdatereliability | NL_MOTHERSTAGE | ความน่าเชื่อถือของวันเกิดเด็ก |
| createid | nl_customer.createid | - | - | ผู้สร้าง |
| createdate | nl_customer.createdate | - | - | วันที่สร้าง |
| updateid | nl_customer.updateid | - | - | ผู้แก้ไข |
| updatedate | nl_customer.updatedate | - | - | วันที่แก้ไข |
| flag_complete | nl_customer.flag_complete | - | - | สถานะความสมบูรณ์ |
| flag_active | nl_customer.flag_active | - | - | สถานะการใช้งาน |
| receivedate | nl_customer.receivedate | - | - | วันที่รับข้อมูล |
| signature | nl_customer.signature | - | - | ลายเซ็น |

### 5.3 ETL Campaign Field Mapping

| Field Name | IC360 Field | JSON Field | Description |
|------------|-------------|------------|-------------|
| campaign_id | - | - | รหัสแคมเปญ |
| parent | nl_contact_campaign.contact_id | - | โปรไฟล์แม่ |
| campaign_name | nl_contact_campaign.campaign_name | - | ชื่อแคมเปญ |
| campaign_type | nl_contact_campaign.campaign_type | - | ประเภทแคมเปญ |
| campaign_status | nl_contact_campaign.campaign_status | - | สถานะแคมเปญ |
| campaign_start_date | nl_contact_campaign.campaign_start_date | - | วันที่เริ่มแคมเปญ |
| campaign_end_date | nl_contact_campaign.campaign_end_date | - | วันที่สิ้นสุดแคมเปญ |
| application_code | nl_contact_campaign.application_code | applicationCode | รหัสแอปพลิเคชัน |
| internal_id | nl_contact_campaign.internal_id | internaIdentifier | รหัสภายใน |
| internal_alternate_id | nl_contact_campaign.internal_alternate_id | internalAlternateIdentifier | รหัสภายในสำรอง |
| create_date | nl_contact_campaign.create_date | createDate | วันที่สร้าง |
| last_update_date | nl_contact_campaign.last_update_date | lastUpdateDate | วันที่อัพเดทล่าสุด |
| date_registration | - | - | วันที่ลงทะเบียน |
| last_updated | - | - | วันที่อัพเดตล่าสุด |

### 5.4 ETL Consent Field Mapping

| Field Name | IC360 Field | JSON Field | Description |
|------------|-------------|------------|-------------|
| consent_id | - | - | รหัสความยินยอม |
| parent | nl_marketing_consent.contact_id / nl_primary_consent.contact_id | - | โปรไฟล์แม่ |
| consent_type | - | - | ประเภทความยินยอม (PRIVACY/MARKETING) |
| consent_status | - | - | สถานะความยินยอม |
| consent_date | nl_marketing_consent.consent_marketing_dt / nl_primary_consent.privacy_13y_dt | consent_date | วันที่ให้ความยินยอม |
| consent_version | nl_marketing_consent.consent_version / nl_primary_consent.consent_version | consent_version | เวอร์ชันความยินยอม |
| is_consented | - | Is_MKT_Subscribed | สถานะการยินยอม (Yes/No) |
| marketing_subscribed_date | - | MKT_Subscribed_Date | วันที่ยินยอมรับข้อมูลการตลาด |
| marketing_subscribed_version | - | MKT_Subscribed_Version | เวอร์ชันการยินยอมรับข้อมูลการตลาด |
| consent_description | - | - | รายละเอียดความยินยอม |
| consent_notes | - | - | หมายเหตุความยินยอม |
| date_registration | - | - | วันที่ลงทะเบียน |
| last_updated | - | - | วันที่อัพเดตล่าสุด |

## 6. IC360 Update Specifications

### 6.1 ETL Main Profile Update
- **ks_contact**
  - Fields:
    - `contact_id`: contact_id (Primary Key)
    - `first_name`: first_name (Required)
    - `last_name`: last_name (Required)
    - `gender`: gender (Default: 'None')
    - `birth_date`: birth_date (Default: '2000-01-01')
    - `contact_source`: contact_source (Default: 'BA')
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists
    - If exists: UPDATE
    - If not exists: INSERT
    - Generate new contact_id if empty or equals uid
  - SQL Queries:
    ```sql
    -- Check if contact exists
    SELECT contact_id 
    FROM ks_contact 
    WHERE contact_id = %(contact_id)s

    -- Update existing contact
    UPDATE ks_contact 
    SET first_name = %(first_name)s,
        last_name = %(last_name)s,
        gender = %(gender)s,
        birth_date = %(birth_date)s,
        contact_source = %(contact_source)s,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s

    -- Insert new contact
    INSERT INTO ks_contact (
        contact_id, first_name, last_name, gender,
        birth_date, contact_source, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(first_name)s, %(last_name)s, %(gender)s,
        %(birth_date)s, %(contact_source)s, NOW()
    )
    ```

- **ks_contact_channel_lineinfo**
  - Fields:
    - `contact_id`: contact_id (Foreign Key)
    - `line_mid`: line_mid
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists
    - If exists: UPDATE line_mid
    - If not exists: INSERT new record
  - SQL Queries:
    ```sql
    -- Check if line info exists
    SELECT contact_id 
    FROM ks_contact_channel_lineinfo 
    WHERE contact_id = %(contact_id)s

    -- Update existing line info
    UPDATE ks_contact_channel_lineinfo 
    SET line_mid = %(line_mid)s,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s

    -- Insert new line info
    INSERT INTO ks_contact_channel_lineinfo (
        contact_id, line_mid, create_dt, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(line_mid)s, NOW(), NOW()
    )
    ```

- **ks_contact_channel_dtl** (Email)
  - Fields:
    - `contact_id`: contact_id (Foreign Key)
    - `channel_type`: 'PE' (Fixed)
    - `channel_info`: email
    - `is_primary`: 1 (Fixed)
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists with channel_type = 'PE'
    - If exists: UPDATE channel_info
    - If not exists: INSERT new record
  - SQL Queries:
    ```sql
    -- Check if email exists
    SELECT contact_id 
    FROM ks_contact_channel_dtl 
    WHERE contact_id = %(contact_id)s
    AND channel_type = 'PE'

    -- Update existing email
    UPDATE ks_contact_channel_dtl 
    SET channel_info = %(email)s,
        is_primary = 1,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s
    AND channel_type = 'PE'

    -- Insert new email
    INSERT INTO ks_contact_channel_dtl (
        contact_id, channel_type, channel_info,
        create_dt, last_upd_dt, addr_seq_no, seq_no, is_primary
    ) VALUES (
        %(contact_id)s, 'PE', %(email)s,
        NOW(), NOW(), 0, 2, 1
    )
    ```

- **ks_contact_channel_dtl** (Mobile)
  - Fields:
    - `contact_id`: contact_id (Foreign Key)
    - `channel_type`: 'M' (Fixed)
    - `channel_info`: phone (replace +66 with 0)
    - `is_primary`: 1 (Fixed)
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists with channel_type = 'M'
    - If exists: UPDATE channel_info
    - If not exists: INSERT new record
  - SQL Queries:
    ```sql
    -- Check if mobile exists
    SELECT contact_id 
    FROM ks_contact_channel_dtl 
    WHERE contact_id = %(contact_id)s
    AND channel_type = 'M'

    -- Update existing mobile
    UPDATE ks_contact_channel_dtl 
    SET channel_info = %(mobile)s,
        is_primary = 1,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s
    AND channel_type = 'M'

    -- Insert new mobile
    INSERT INTO ks_contact_channel_dtl (
        contact_id, channel_type, channel_info,
        create_dt, last_upd_dt, addr_seq_no, seq_no, is_primary
    ) VALUES (
        %(contact_id)s, 'M', %(mobile)s,
        NOW(), NOW(), 0, 1, 1
    )
    ```

- **nl_ks_contact**
  - Fields:
    - `contact_id`: contact_id (Primary Key)
    - `flag_complete`: 'C' (Default)
    - `register_date`: date_registration
    - `agent_referral_code`: nestle_agent_referral_code
    - `sourceid`: sourceid
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists
    - If exists: UPDATE
    - If not exists: INSERT
  - SQL Queries:
    ```sql
    -- Check if nl_ks_contact exists
    SELECT contact_id 
    FROM nl_ks_contact 
    WHERE contact_id = %(contact_id)s

    -- Update existing nl_ks_contact
    UPDATE nl_ks_contact 
    SET flag_complete = %(flag_complete)s,
        register_date = %(register_date)s,
        agent_referral_code = %(agent_referral_code)s,
        sourceid = %(sourceid)s,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s

    -- Insert new nl_ks_contact
    INSERT INTO nl_ks_contact (
        contact_id, flag_complete, register_date,
        agent_referral_code, sourceid, create_dt, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(flag_complete)s, %(register_date)s,
        %(agent_referral_code)s, %(sourceid)s, NOW(), NOW()
    )
    ```

- **ks_contact_addr_dtl**
  - Fields:
    - `contact_id`: contact_id (Foreign Key)
    - `address_type`: 'HOME' (Fixed)
    - `addr_1`: address
    - `sub_district`: sub_district
    - `city`: city
    - `state_code`: state_code
    - `postal_code`: postal_code
    - `country_code`: 'TH' (Fixed)
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id exists with address_type = 'HOME'
    - If exists: UPDATE address fields
    - If not exists: INSERT new record
  - SQL Queries:
    ```sql
    -- Check if address exists
    SELECT contact_id 
    FROM ks_contact_addr_dtl 
    WHERE contact_id = %(contact_id)s
    AND address_type = 'HOME'

    -- Update existing address
    UPDATE ks_contact_addr_dtl 
    SET addr_1 = %(addr_1)s,
        sub_district = %(sub_district)s,
        city = %(city)s,
        state_code = %(state_code)s,
        postal_code = %(postal_code)s,
        country_code = 'TH',
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s
    AND address_type = 'HOME'

    -- Insert new address
    INSERT INTO ks_contact_addr_dtl (
        contact_id, address_type, addr_1,
        sub_district, city, state_code,
        postal_code, country_code,
        create_dt, last_upd_dt, addr_seq_no
    ) VALUES (
        %(contact_id)s, 'HOME', %(addr_1)s,
        %(sub_district)s, %(city)s, %(state_code)s,
        %(postal_code)s, 'TH',
        NOW(), NOW(), 1
    )
    ```

### 6.2 ETL Child Update
- **nl_customer**
  - Fields:
    - `cusid`: cusid (Primary Key)
    - `motherid`: motherid (Foreign Key to ks_contact)
    - `fname`: fname (Required)
    - `lname`: lname (Required)
    - `nname`: nname
    - `gender`: gender (Default: 'None')
    - `birthdate`: birthdate
    - `reasonid`: reasonid
    - `reason`: reason
    - `remark`: remark
    - `signature`: signature (Default: 'N')
    - `updateid`: '0' (Fixed)
    - `updatedate`: NOW()
    - `flag_complete`: flag_complete (Default: 'C')
    - `flag_active`: flag_active (Default: '1')
    - `firstpro`: firstpro
    - `firstformula`: firstformula
    - `lastpro`: lastpro
    - `lastformula`: lastformula
    - `receivedate`: receivedate
  - Update Logic:
    - Check if cusid exists
    - If exists: UPDATE
    - If not exists: INSERT
    - Generate new cusid if empty
  - SQL Queries:
    ```sql
    -- Check if customer exists
    SELECT cusid 
    FROM nl_customer 
    WHERE cusid = %(cusid)s

    -- Update existing customer
    UPDATE nl_customer 
    SET motherid = %(motherid)s,
        fname = %(fname)s,
        lname = %(lname)s,
        nname = %(nname)s,
        gender = %(gender)s,
        birthdate = %(birthdate)s,
        reasonid = %(reasonid)s,
        reason = %(reason)s,
        remark = %(remark)s,
        signature = %(signature)s,
        updateid = '0',
        updatedate = NOW(),
        flag_complete = %(flag_complete)s,
        flag_active = %(flag_active)s,
        firstpro = %(firstpro)s,
        firstformula = %(firstformula)s,
        lastpro = %(lastpro)s,
        lastformula = %(lastformula)s
    WHERE cusid = %(cusid)s

    -- Insert new customer
    INSERT INTO nl_customer (
        cusid, motherid, fname, lname, nname,
        gender, birthdate, reasonid, reason, remark,
        signature, createid, createdate, updateid, updatedate,
        flag_complete, flag_active, firstpro, firstformula,
        lastpro, lastformula, receivedate
    ) VALUES (
        %(cusid)s, %(motherid)s, %(fname)s, %(lname)s, %(nname)s,
        %(gender)s, %(birthdate)s, %(reasonid)s, %(reason)s, %(remark)s,
        %(signature)s, '0', NOW(), '0', NOW(),
        %(flag_complete)s, %(flag_active)s, %(firstpro)s, %(firstformula)s,
        %(lastpro)s, %(lastformula)s, %(receivedate)s
    )
    ```

- **nl_customer_moreinfo**
  - Fields:
    - `cusid`: cusid (Primary Key)
    - `motherid`: motherid (Foreign Key to ks_contact)
    - `born_place_id`: born_place_id (Default: 0)
    - `born_place_type`: born_place_type (Default: '-')
    - `birth_plan`: birth_plan (Default: '-')
    - `mother_prod_id`: mother_prod_id (Default: 0)
    - `current_mother_prod_id`: current_mother_prod_id (Default: 0)
    - `pc_code`: pc_code (preserve existing value if not empty)
  - Update Logic:
    - Check if cusid exists
    - If exists: UPDATE (preserve pc_code if exists)
    - If not exists: INSERT
  - SQL Queries:
    ```sql
    -- Check if moreinfo exists
    SELECT cusid 
    FROM nl_customer_moreinfo 
    WHERE cusid = %(cusid)s

    -- Check existing pc_code
    SELECT pc_code 
    FROM nl_customer_moreinfo 
    WHERE cusid = %(cusid)s

    -- Update existing moreinfo
    UPDATE nl_customer_moreinfo 
    SET born_place_id = %(born_place_id)s,
        born_place_type = %(born_place_type)s,
        birth_plan = %(birth_plan)s,
        mother_prod_id = %(mother_prod_id)s,
        current_mother_prod_id = %(current_mother_prod_id)s,
        pc_code = %(pc_code)s,
        motherid = %(motherid)s
    WHERE cusid = %(cusid)s

    -- Insert new moreinfo
    INSERT INTO nl_customer_moreinfo (
        cusid, motherid, born_place_id, born_place_type,
        birth_plan, mother_prod_id, current_mother_prod_id,
        pc_code
    ) VALUES (
        %(cusid)s, %(motherid)s, %(born_place_id)s, %(born_place_type)s,
        %(birth_plan)s, %(mother_prod_id)s, %(current_mother_prod_id)s,
        %(pc_code)s
    )
    ```

### 6.3 ETL Consent Update
- **nl_marketing_consent**
  - Fields:
    - `contact_id`: parent (Primary Key)
    - `channel`: channel (Primary Key)
    - `consent_marketing`: is_consented
    - `consent_marketing_dt`: marketing_subscribed_date
    - `consent_version`: marketing_subscribed_version
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id and channel exist
    - If exists: UPDATE
    - If not exists: INSERT
  - SQL Queries:
    ```sql
    -- Check if marketing consent exists
    SELECT contact_id 
    FROM nl_marketing_consent 
    WHERE contact_id = %(contact_id)s
    AND channel = %(channel)s

    -- Update existing marketing consent
    UPDATE nl_marketing_consent 
    SET consent_marketing = %(consent_marketing)s,
        consent_marketing_dt = %(consent_marketing_dt)s,
        consent_version = %(consent_version)s,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s
    AND channel = %(channel)s

    -- Insert new marketing consent
    INSERT INTO nl_marketing_consent (
        contact_id, channel, consent_marketing,
        consent_marketing_dt, consent_version,
        create_dt, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(channel)s, %(consent_marketing)s,
        %(consent_marketing_dt)s, %(consent_version)s,
        NOW(), NOW()
    )
    ```

- **nl_primary_consent**
  - Fields:
    - `contact_id`: parent (Primary Key)
    - `register_dt`: register_dt (Primary Key)
    - `channel`: channel (Primary Key)
    - `consent_privacy_13y`: is_consented
    - `privacy_13y_dt`: consent_date
    - `consent_version`: consent_version
    - `last_upd_dt`: NOW()
  - Update Logic:
    - Check if contact_id, register_dt, and channel exist
    - If exists: UPDATE
    - If not exists: INSERT
  - SQL Queries:
    ```sql
    -- Check if privacy consent exists
    SELECT contact_id 
    FROM nl_primary_consent 
    WHERE contact_id = %(contact_id)s
    AND register_dt = %(register_dt)s
    AND channel = %(channel)s

    -- Update existing privacy consent
    UPDATE nl_primary_consent 
    SET consent_privacy_13y = %(consent_privacy_13y)s,
        privacy_13y_dt = %(privacy_13y_dt)s,
        consent_version = %(consent_version)s,
        last_upd_dt = NOW()
    WHERE contact_id = %(contact_id)s
    AND register_dt = %(register_dt)s
    AND channel = %(channel)s

    -- Insert new privacy consent
    INSERT INTO nl_primary_consent (
        contact_id, register_dt, channel,
        consent_privacy_13y, privacy_13y_dt,
        consent_version, create_dt, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(register_dt)s, %(channel)s,
        %(consent_privacy_13y)s, %(privacy_13y_dt)s,
        %(consent_version)s, NOW(), NOW()
    )
    ```

### 6.4 ETL Campaign Update
- **nl_contact_campaign**
  - Fields:
    - `contact_id`: parent (Primary Key)
    - `application_code`: application_code (Primary Key)
    - `internal_id`: internal_id (Primary Key)
    - `internal_alternate_id`: internal_alternate_id (Primary Key)
    - `create_dt`: create_date
    - `last_upd_dt`: last_update_date
  - Update Logic:
    - Check if composite key (contact_id, application_code, internal_id, internal_alternate_id) exists
    - If exists: UPDATE last_upd_dt
    - If not exists: INSERT
  - SQL Queries:
    ```sql
    -- Check if campaign exists
    SELECT contact_id 
    FROM nl_contact_campaign 
    WHERE contact_id = %(contact_id)s
    AND application_code = %(application_code)s
    AND internal_id = %(internal_id)s
    AND internal_alternate_id = %(internal_alternate_id)s

    -- Update existing campaign
    UPDATE nl_contact_campaign 
    SET last_upd_dt = %(last_upd_dt)s
    WHERE contact_id = %(contact_id)s
    AND application_code = %(application_code)s
    AND internal_id = %(internal_id)s
    AND internal_alternate_id = %(internal_alternate_id)s

    -- Insert new campaign
    INSERT INTO nl_contact_campaign (
        contact_id, application_code, internal_id,
        internal_alternate_id, create_dt, last_upd_dt
    ) VALUES (
        %(contact_id)s, %(application_code)s, %(internal_id)s,
        %(internal_alternate_id)s, %(create_dt)s, %(last_upd_dt)s
    )
    ```

### 6.5 Update Rules
1. **Contact ID Generation**
   - If contact_id is empty or equals uid:
     - Generate new contact_id
     - Update all related records (child, consent, campaign)
     - Update contact_id in current record

2. **Default Values**
   - gender: 'None' if empty
   - birth_date: '2000-01-01' if empty
   - contact_source: 'BA' if empty
   - income: '0' if empty
   - flag_complete: 'C' if empty
   - flag_active: '1' if empty
   - signature: 'N' if empty
   - createid: '0' if empty
   - updateid: '0'
   - country_code: 'TH'

3. **Phone Number Format**
   - Replace '+66' with '0' for mobile numbers

4. **PC Code Preservation**
   - If pc_code exists in IC360 and is not empty, preserve the existing value

5. **Timestamp Updates**
   - Use NOW() for last_upd_dt
   - Use NOW() for create_dt in new records

6. **Error Handling**
   - Log all SQL queries and parameters
   - Log errors with detailed messages
   - Raise exceptions for critical errors
   - Update related records only after successful main record update

## 7. Webhook Integration Status

### 7.1 Webhook Inbound (Completed)
- ระบบสามารถรับข้อมูลจาก API ภายนอกผ่าน Webhook ได้อย่างถูกต้อง
- ข้อมูลที่ได้รับจะถูกประมวลผลโดย DataHubProcessor และบันทึกลงฐานข้อมูล
- การประมวลผลข้อมูลมีการจัดการความผิดพลาดและบันทึก log สำหรับการตรวจสอบ

#### 7.1.1 กระบวนการประมวลผลข้อมูลจาก Webhook
1. **การรับข้อมูล**: ระบบรับ JSON payload จาก webhook และส่งต่อไปยัง `DataHubProcessor`
2. **การแยกและประมวลผลข้อมูล**:
   - โปรไฟล์: ข้อมูลหลักของลูกค้าถูกประมวลผลโดย `ProfileProcessor`
   - ข้อมูลเด็ก: ข้อมูลเด็กถูกประมวลผลโดย `ChildProcessor`
   - แคมเปญ: ข้อมูลแคมเปญถูกประมวลผลโดย `CampaignProcessor`
   - ความยินยอม: ข้อมูลความยินยอมถูกประมวลผลโดย `ConsentProcessor`
3. **การแปลงข้อมูล**: ข้อมูลที่ได้รับถูกแปลงให้สอดคล้องกับโครงสร้าง DocType ของ DataHub
4. **การค้นหาและอัปเดตข้อมูล Lookup**: ข้อมูลจะถูกแปลงตาม lookup table ที่กำหนดไว้
5. **การบันทึกข้อมูล**: ข้อมูลถูกบันทึกลงในฐานข้อมูล Frappe
6. **การบันทึก log**: ระบบบันทึก log ทุกขั้นตอนเพื่อการตรวจสอบและแก้ไขปัญหา

### 7.2 Webhook Outbound (Pending)
- อยู่ระหว่างการพัฒนาระบบสำหรับส่งข้อมูลไปยังระบบภายนอก
- จะใช้ DocType `DH Webhook Outbound` เพื่อเก็บข้อมูลที่ต้องการส่งและสถานะการส่ง
- มีแผนในการพัฒนาระบบ retry สำหรับการส่งข้อมูลที่ไม่สำเร็จ

### 7.3 Flow Diagram
```
[ระบบภายนอก] --webhook payload--> [DataHub Webhook Inbound] --> [DataHubProcessor]
                                                                   |
                                                                   |--> [ProfileProcessor]
                                                                   |--> [ChildProcessor]
                                                                   |--> [CampaignProcessor]
                                                                   |--> [ConsentProcessor]
                                                                   |--> [Update Lookup Data]
                                                                   |
[ระบบภายนอก] <--webhook outbound-- [DataHub Webhook Outbound] <-- [Frappe Database]
```

## 8. DataHub to IC360 Synchronization

### 8.1 การซิงค์ข้อมูลจาก DataHub ไปยัง IC360
ระบบ DataHub มีความสามารถในการซิงค์ข้อมูลที่มีอยู่ในระบบไปยังฐานข้อมูล IC360 ผ่านการใช้งาน `IC360Client` โดยมีองค์ประกอบหลักดังนี้:

1. **กลไกการซิงค์ข้อมูล**: ระบบจะซิงค์ข้อมูลจาก DataHub ไปยัง IC360 ผ่านฟังก์ชัน `sync_to_ic360` ซึ่งรองรับทั้งการซิงค์แบบเลือกเฉพาะโปรไฟล์ และการซิงค์ทั้งหมด

2. **การแปลงข้อมูล Lookup**: ก่อนที่จะส่งโปรไฟล์ไปยัง IC360 ระบบจะแปลงข้อมูลตาม lookup table ที่กำหนดไว้

3. **IC360Processor**: คลาสที่จัดการกับการอัพเดทข้อมูลในฐานข้อมูล IC360 ประกอบด้วยเมธอดต่างๆ สำหรับการอัพเดทข้อมูลแต่ละประเภท:
   - `update_profile`: อัพเดทข้อมูลโปรไฟล์
   - `update_child`: อัพเดทข้อมูลเด็ก
   - `update_consent`: อัพเดทข้อมูลความยินยอม
   - `update_campaign`: อัพเดทข้อมูลแคมเปญ

4. **การบันทึก Sync Log**: ทุกการซิงค์ข้อมูลจะมีการบันทึก log ในตาราง `ETL Sync Log` เพื่อใช้ในการติดตามและตรวจสอบ

### 8.2 กระบวนการทำงาน
1. **เริ่มต้นการซิงค์**:
   - ผู้ใช้เรียกใช้งานฟังก์ชัน `sync_to_ic360` โดยระบุ profile_id (หรือไม่ระบุเพื่อซิงค์ทั้งหมด)
   - ระบบสร้าง Sync Log เพื่อบันทึกการทำงาน

2. **ดึงข้อมูลจาก DataHub**:
   - ถ้าระบุ profile_id: ดึงข้อมูลเฉพาะโปรไฟล์นั้น
   - ถ้าไม่ระบุ: ดึงโปรไฟล์ทั้งหมดที่ยังไม่ได้ซิงค์ (โดยใช้ฟิลด์ is_synced_to_ic360)

3. **วนลูปแต่ละโปรไฟล์**:
   - แปลงข้อมูล lookup ก่อนส่งไปยัง IC360
   - อัพเดทข้อมูลโปรไฟล์ไปยัง IC360
   - ดึงและอัพเดทข้อมูลเด็กที่เกี่ยวข้อง
   - ดึงและอัพเดทข้อมูลความยินยอม
   - ดึงและอัพเดทข้อมูลแคมเปญ

4. **จัดการความผิดพลาด**:
   - จัดการความผิดพลาดในแต่ละโปรไฟล์แยกกัน
   - บันทึกผลลัพธ์ทั้งสำเร็จและไม่สำเร็จ

5. **อัพเดทสถานะในระบบ**:
   - อัพเดทสถานะการซิงค์ในแต่ละโปรไฟล์
   - อัพเดท Sync Log ด้วยผลลัพธ์ทั้งหมด

### 8.3 IC360Client
ไลบรารี `IC360Client` ทำหน้าที่เชื่อมต่อกับฐานข้อมูล IC360 และรัน SQL query ต่างๆ โดยมีคุณสมบัติดังนี้:

1. **การจัดการการเชื่อมต่อ**:
   - สร้างการเชื่อมต่อเมื่อมีการเรียกใช้งาน
   - จัดการการปิดการเชื่อมต่อเมื่อทำงานเสร็จ

2. **การรัน SQL Query**:
   - รองรับการทำ SELECT, INSERT, UPDATE, DELETE
   - จัดการ transaction และ rollback เมื่อเกิดข้อผิดพลาด

3. **การจัดการความผิดพลาด**:
   - บันทึกข้อผิดพลาดในกรณีที่เกิดปัญหาในการเชื่อมต่อหรือการรันคำสั่ง SQL

### 8.4 SQL Queries
ระบบใช้ SQL queries ตามที่กำหนดไว้ใน System Design ส่วนที่ 6 (IC360 Update Specifications) เพื่อตรวจสอบว่าข้อมูลมีอยู่แล้วหรือไม่ และดำเนินการ INSERT หรือ UPDATE ตามความเหมาะสม

### 8.5 Flow Diagram
```
[DataHub]  -->  [sync_to_ic360]  -->  [IC360Processor]
    |                                        |
    |                                        v
[ETL Sync Log]  <--  [Error Handling]  <--  [IC360Client]  -->  [IC360 Database]
```

### 8.6 สถานะการพัฒนา
- [x] การเชื่อมต่อกับ IC360 ด้วย IC360Client
- [x] การแปลงข้อมูล Lookup ระหว่าง DataHub และ IC360
- [x] การสร้าง SQL queries สำหรับการ INSERT และ UPDATE ข้อมูล
- [ ] การสร้างระบบ Scheduled Jobs สำหรับการซิงค์อัตโนมัติ
- [ ] การพัฒนาระบบจัดการข้อผิดพลาดและการ retry
- [ ] การทดสอบเต็มรูปแบบกับฐานข้อมูล IC360 จริง

