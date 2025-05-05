import frappe
from datetime import datetime

def transform_profile_data(data):
    """แปลงข้อมูลโปรไฟล์จาก JSON ให้เข้ากับโครงสร้าง ETL Main Profile"""
    return {
        # Basic Info
        "uid": data.get("uid"),
        "first_name": data.get("firstname"),
        "last_name": data.get("lastname"),
        "gender_sd": data.get("gender"),
        "birth_date": data.get("mom_birthdate"),
        
        # Contact Info
        "phone": data.get("phonenumber"),
        "email": data.get("email"),
        "line_mid": data.get("line_mid"),
        
        # Address Info
        "address": data.get("addressline1"),
        "province_name": data.get("region"),
        "amphur_name": data.get("city"),
        "sub_district_name": data.get("addressline2"),
        "postal_code": data.get("zip"),
        
        # Additional Info
        "income": data.get("income"),
        "contact_source": data.get("contact_source"),
        "brand": data.get("brand"),
        "status": data.get("status"),
        "data_source_code": data.get("data_source_code"),
        "nestle_agent_referral_code": data.get("nestle_agent_referral_code"),
        
        # Marketing Consent Info
        "is_consented": data.get("Is_MKT_Subscribed"),
        "marketing_subscribed_date": data.get("MKT_Subscribed_Date"),
        "marketing_subscribed_version": data.get("MKT_Subscribed_Version"),
        
        # Child Info
        "gg_hospital": data.get("gg_hospital"),
        "gg_child_delivery_type": data.get("gg_child_delivery_type"),
        "gg_milk_currently_consuming": data.get("gg_milk_currently_consuming"),
        "child_birthdatereliability": data.get("child_birthdatereliability"),
        
        # System Info
        "date_registration": data.get("date_registration"),
        "last_updated": data.get("last_updated") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_child_data(data, parent_id=None):
    """แปลงข้อมูลเด็กจาก JSON ให้เข้ากับโครงสร้าง ETL Child"""
    return {
        # Basic Info
        "cusid": data.get("child_id"),
        "motherid": parent_id,  # motherid ใช้เชื่อมโยงกับ ETL Main Profile
        "fname": data.get("child_firstname"),
        "lname": "",  # ไม่มีใน JSON
        "nname": data.get("child_firstname"),
        "birthdate": data.get("child_birthdate"),
        
        # Child Details
        "reason": data.get("reason"),
        "pc_code": data.get("pc_code"),
        "mother_prod_id": data.get("old_mother_prod"),
        "current_mother_prod_id": data.get("current_mother_prod"),
        
        # Default values ตามที่ระบุในเอกสาร
        # "gender": "None",
        # "flag_complete": "C",
        # "flag_active": "1",
        # "signature": "N",
        # "createid": "0",
        # "updateid": "0",
        # "createdate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # "updatedate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # "receivedate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_campaign_data(data, parent_id=None):
    """แปลงข้อมูลแคมเปญจาก JSON ให้เข้ากับโครงสร้าง ETL Campaign"""
    # สร้าง campaign_id ถ้าไม่มี
    campaign_id = f"CAM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{data.get('applicationCode', '')}"
    
    return {
        # Basic Info
        "campaign_id": campaign_id,
        "contact_id": parent_id,  # contact_id ใช้เชื่อมโยงกับ ETL Main Profile
        
        # Campaign Info
        "campaign_name": data.get("campaignName", ""),
        "campaign_type": data.get("campaignType", ""),
        "campaign_status": data.get("campaignStatus", ""),
        "campaign_start_date": data.get("campaignStartDate"),
        "campaign_end_date": data.get("campaignEndDate"),
        
        # Application Info
        "application_code": data.get("applicationCode"),
        "internal_id": data.get("internaIdentifier"),
        "internal_alternate_id": data.get("internalAlternateIdentifier", ""),
        "create_date": data.get("createDate") ,
        "last_update_date": data.get("lastUpdateDate"),
        
        # System Info
        "date_registration": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_consent_data(data, parent_id=None, consent_type="MARKETING"):
    """แปลงข้อมูลความยินยอมจาก JSON ให้เข้ากับโครงสร้าง ETL Consent"""
    # สร้าง consent_id ถ้าไม่มี
    consent_id = f"CON-{datetime.now().strftime('%Y%m%d%H%M%S')}-{consent_type}"
    
    # กำหนดค่าเริ่มต้นสำหรับข้อมูลความยินยอม
    consent ={
        # Basic Info
        "consent_id": consent_id,
        "contact_id": parent_id,  # contact_id ใช้เชื่อมโยงกับ ETL Main Profile
        
        # Consent Info
        "consent_type": consent_type,
        "consent_status": "Active",
        "is_consented": "Yes" ,
        # "consent_date": data.get("consent_date") ,
        # "consent_version": data.get("consent_version") ,
  
        
        # Consent Details
        "consent_description": "",
        "consent_notes": "",
        
        # System Info
        "date_registration": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if consent_type == "MARKETING":
        consent.update({
            "consent_date": data.get("MKT_Subscribed_Date") ,
            "consent_version": data.get("MKT_Subscribed_Version") ,
        })
    else:
        consent.update({
            "consent_date": data.get("consent_date") ,
            "consent_version": data.get("consent_version") ,
        })
    
    result = consent
    
    # ถ้าเป็น Marketing Consent ให้เพิ่มข้อมูลเฉพาะ
    # if consent_type == "MARKETING":
    #     result.update({
    #         "consent_date": data.get("MKT_Subscribed_Date"),
    #         "consent_version": data.get("MKT_Subscribed_Version")
    #     })
    
    return result

def transform_contact_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - ks_contact"""
    return {
        "contact_id": profile_data.get("contact_id"),
        "first_name": profile_data.get("first_name") or "",
        "last_name": profile_data.get("last_name") or "",
        "gender": profile_data.get("gender") or "None",
        "birth_date": profile_data.get("birth_date") or "2000-01-01",
        "contact_source": profile_data.get("contact_source") or "BA",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_line_info_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - ks_contact_channel_lineinfo"""
    return {
        "contact_id": profile_data.get("contact_id"),
        "line_mid": profile_data.get("line_mid") or "",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_email_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - ks_contact_channel_dtl (Email)"""
    return {
        "contact_id": profile_data.get("contact_id"),
        "channel_type": "PE",
        "channel_info": profile_data.get("email") or "",
        "is_primary": 1,
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_mobile_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - ks_contact_channel_dtl (Mobile)"""
    phone = profile_data.get("phone") or ""
    # แปลงเบอร์ +66 เป็น 0
    if phone.startswith("+66"):
        phone = "0" + phone[3:]
        
    return {
        "contact_id": profile_data.get("contact_id"),
        "channel_type": "M",
        "channel_info": phone,
        "is_primary": 1,
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_nl_ks_contact_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_ks_contact"""
    return {
        "contact_id": profile_data.get("contact_id"),
        "flag_complete": "C",
        "register_date": profile_data.get("date_registration") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_referral_code": profile_data.get("nestle_agent_referral_code") or "",
        "sourceid": profile_data.get("sourceid") or profile_data.get("data_source_code") or "",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_address_for_ic360(profile_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - ks_contact_addr_dtl"""
    return {
        "contact_id": profile_data.get("contact_id"),
        "address_type": "HOME",
        "addr_1": profile_data.get("address") or "",
        "sub_district": profile_data.get("sub_district") or "",
        "city": profile_data.get("city") or "",
        "state_code": profile_data.get("state_code") or "",
        "postal_code": profile_data.get("postal_code") or "",
        "country_code": "TH",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_child_for_ic360(child_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_customer"""
    return {
        "cusid": child_data.get("cusid"),
        "motherid": child_data.get("motherid"),
        "fname": child_data.get("fname") or "",
        "lname": child_data.get("lname") or "",
        "nname": child_data.get("nname") or "",
        "gender": child_data.get("gender") or "None",
        "birthdate": child_data.get("birthdate") or "",
        "reasonid": child_data.get("reasonid") or "",
        "reason": child_data.get("reason") or "",
        "remark": child_data.get("remark") or "",
        "signature": child_data.get("signature") or "N",
        "updateid": "0",
        "updatedate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flag_complete": child_data.get("flag_complete") or "C",
        "flag_active": child_data.get("flag_active") or "1",
        "firstpro": child_data.get("firstpro") or "",
        "firstformula": child_data.get("firstformula") or "",
        "lastpro": child_data.get("lastpro") or "",
        "lastformula": child_data.get("lastformula") or "",
        "receivedate": child_data.get("receivedate") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_child_moreinfo_for_ic360(child_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_customer_moreinfo"""
    return {
        "cusid": child_data.get("cusid"),
        "motherid": child_data.get("motherid"),
        "born_place_id": child_data.get("born_place_id") or "0",
        "born_place_type": child_data.get("born_place_type") or "-",
        "birth_plan": child_data.get("birth_plan") or "-",
        "mother_prod_id": child_data.get("mother_prod_id") or "0",
        "current_mother_prod_id": child_data.get("current_mother_prod_id") or "0",
        "pc_code": child_data.get("pc_code") or "",
        "mother_stage": child_data.get("mother_stage") or ""
    }

def transform_marketing_consent_for_ic360(consent_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_marketing_consent"""
    return {
        "contact_id": consent_data.get("contact_id"),
        "channel": consent_data.get("consent_channel") or "WEB",
        "consent_marketing": consent_data.get("is_consented") or "No",
        "consent_marketing_dt": consent_data.get("consent_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "consent_version": consent_data.get("consent_version") or "1",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_primary_consent_for_ic360(consent_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_primary_consent"""
    return {
        "contact_id": consent_data.get("contact_id"),
        "register_dt": consent_data.get("date_registration") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": consent_data.get("consent_channel") or "WEB",
        "consent_privacy_13y": consent_data.get("is_consented") or "No",
        "privacy_13y_dt": consent_data.get("consent_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "consent_version": consent_data.get("consent_version") or "1",
        "last_upd_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_campaign_for_ic360(campaign_data):
    """แปลงข้อมูลสำหรับอัพเดทในระบบ IC360 - nl_contact_campaign"""
    return {
        "contact_id": campaign_data.get("contact_id"),
        "application_code": campaign_data.get("application_code") or "",
        "internal_id": campaign_data.get("internal_id") or "",
        "internal_alternate_id": campaign_data.get("internal_alternate_id") or "",
        "create_dt": campaign_data.get("create_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_upd_dt": campaign_data.get("last_update_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def transform_webhook_to_sync_log(webhook_data):
    """แปลงข้อมูลจาก webhook เพื่อสร้าง sync log"""
    sync_id = f"SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "sync_id": sync_id,
        "sync_type": "PENDING",
        "sync_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending",
        "total_records": 1,
        "processed_records": 0,
        "raw_data": frappe.as_json(webhook_data),
        "error_log": ""
    } 