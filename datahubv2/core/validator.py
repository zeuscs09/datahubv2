import frappe
import re
from datetime import datetime

def validate_profile_data(data):
    """ตรวจสอบความถูกต้องของข้อมูลโปรไฟล์"""
    # ตรวจสอบฟิลด์ที่จำเป็น
    required_fields = ["uid", "phonenumber", "firstname", "lastname"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        frappe.log_error(f"Missing required fields: {', '.join(missing_fields)}", "Profile Validation Error")
        return False
    
    # ตรวจสอบรูปแบบเบอร์โทร
    if data.get("phonenumber"):
        phone = data.get("phonenumber")
        # รองรับเบอร์โทรไทยทั้งรูปแบบ 0XXXXXXXXX และ +66XXXXXXXXX
        if not (re.match(r"^0\d{9}$", phone) or re.match(r"^\+66\d{9}$", phone)):
            frappe.log_error(f"Invalid phone number format: {phone}", "Profile Validation Error")
            return False
    
    # ตรวจสอบรูปแบบอีเมล
    if data.get("email"):
        email = data.get("email")
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            frappe.log_error(f"Invalid email format: {email}", "Profile Validation Error")
            return False
    
    # ตรวจสอบรูปแบบวันที่
    for date_field in ["date_registration", "last_updated", "mom_birthdate", "MKT_Subscribed_Date", "consent_date"]:
        if data.get(date_field):
            try:
                if ":" in data.get(date_field):  # รูปแบบ YYYY-MM-DD HH:MM:SS
                    datetime.strptime(data.get(date_field), "%Y-%m-%d %H:%M:%S")
                else:  # รูปแบบ YYYY-MM-DD
                    datetime.strptime(data.get(date_field), "%Y-%m-%d")
            except ValueError:
                frappe.log_error(f"Invalid date format for {date_field}: {data.get(date_field)}", "Profile Validation Error")
                return False
    
    return True

def validate_child_data(data):
    """ตรวจสอบความถูกต้องของข้อมูลเด็ก"""
    # ตรวจสอบฟิลด์ที่จำเป็น
    required_fields = ["child_birthdate"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        frappe.log_error(f"Missing required fields: {', '.join(missing_fields)}", "Child Validation Error")
        return False
    
    # ตรวจสอบรูปแบบวันเกิด
    if data.get("child_birthdate"):
        try:
            datetime.strptime(data.get("child_birthdate"), "%Y-%m-%d")
        except ValueError:
            frappe.log_error(f"Invalid birthdate format: {data.get('child_birthdate')}", "Child Validation Error")
            return False
    
    # ตรวจสอบวันที่เพิ่มข้อมูลเด็ก
    if data.get("child_add_date"):
        try:
            datetime.strptime(data.get("child_add_date"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            frappe.log_error(f"Invalid add date format: {data.get('child_add_date')}", "Child Validation Error")
            return False
    
    return True

def validate_campaign_data(data):
    """ตรวจสอบความถูกต้องของข้อมูลแคมเปญ"""
    # ตรวจสอบฟิลด์ที่จำเป็น
    required_fields = ["applicationCode", "internaIdentifier"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        frappe.log_error(f"Missing required fields: {', '.join(missing_fields)}", "Campaign Validation Error")
        return False
    
    # ตรวจสอบวันที่สร้างและอัพเดท
    for date_field in ["createDate", "lastUpdateDate"]:
        if data.get(date_field):
            try:
                datetime.strptime(data.get(date_field), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                frappe.log_error(f"Invalid date format for {date_field}: {data.get(date_field)}", "Campaign Validation Error")
                return False
    
    return True

def validate_marketing_consent_data(data):
    """ตรวจสอบความถูกต้องของข้อมูลความยินยอม"""
    # สำหรับ consent มักจะรวมกับข้อมูลโปรไฟล์ ตรวจสอบฟิลด์ที่เกี่ยวข้อง
    has_marketing_consent = data.get("Is_MKT_Subscribed") is not None
    has_marketing_date = data.get("MKT_Subscribed_Date") is not None
    has_marketing_version = data.get("MKT_Subscribed_Version") is not None
    
    # ถ้ามีการยินยอมด้านการตลาด ต้องมีวันที่และเวอร์ชัน
    if has_marketing_consent and (not has_marketing_date or not has_marketing_version):
        frappe.log_error("Marketing consent requires date and version", "Consent Validation Error")
        return False
    
    # ตรวจสอบรูปแบบวันที่
    if has_marketing_date:
        try:
            datetime.strptime(data.get("MKT_Subscribed_Date"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            frappe.log_error(f"Invalid marketing consent date format: {data.get('MKT_Subscribed_Date')}", "Consent Validation Error")
            return False
    
    # ตรวจสอบค่าการยินยอม
    if has_marketing_consent and data.get("Is_MKT_Subscribed") not in ["Yes", "No"]:
        frappe.log_error(f"Invalid marketing consent value: {data.get('Is_MKT_Subscribed')}, expected 'Yes' or 'No'", "Consent Validation Error")
        return False
    
    return True

def validate_privacy_consent_data(data):
    """ตรวจสอบความถูกต้องของข้อมูลความยินยอม"""
    # สำหรับ consent มักจะรวมกับข้อมูลโปรไฟล์ ตรวจสอบฟิลด์ที่เกี่ยวข้อง
    consent_date = data.get("consent_date") is not None
    consent_version = data.get("consent_version") is not None
    
    # ถ้ามีการยินยอมด้านการตลาด ต้องมีวันที่และเวอร์ชัน
    if consent_date and (not consent_date or not consent_version):
        frappe.log_error("Marketing consent requires date and version", "Consent Validation Error")
        return False
    
    # ตรวจสอบรูปแบบวันที่
    if consent_date:
        try:
            datetime.strptime(data.get("consent_date"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            frappe.log_error(f"Invalid marketing consent date format: {data.get('consent_date')}", "Consent Validation Error")
            return False
    
    
    return True


def validate_profile_db_update(profile_data):
    """ตรวจสอบความถูกต้องของข้อมูลโปรไฟล์สำหรับการอัพเดทฐานข้อมูล"""
    if not profile_data.get("contact_id") and not profile_data.get("uid"):
        frappe.log_error("Missing both contact_id and uid", "Profile DB Update Validation Error")
        return False
    
    return True

def validate_child_db_update(child_data):
    """ตรวจสอบความถูกต้องของข้อมูลเด็กสำหรับการอัพเดทฐานข้อมูล"""
    if not child_data.get("cusid"):
        frappe.log_error("Missing cusid", "Child DB Update Validation Error")
        return False
    
    if not child_data.get("motherid"):
        frappe.log_error("Missing motherid", "Child DB Update Validation Error")
        return False
    
    return True

def validate_campaign_db_update(campaign_data):
    """ตรวจสอบความถูกต้องของข้อมูลแคมเปญสำหรับการอัพเดทฐานข้อมูล"""
    if not campaign_data.get("contact_id") and not campaign_data.get("contact_id"):
        frappe.log_error("Missing contact_id/parent", "Campaign DB Update Validation Error")
        return False
    
    if not campaign_data.get("application_code"):
        frappe.log_error("Missing application_code", "Campaign DB Update Validation Error")
        return False
    
    if not campaign_data.get("internal_id"):
        frappe.log_error("Missing internal_id", "Campaign DB Update Validation Error")
        return False
    
    return True

def validate_consent_db_update(consent_data):
    """ตรวจสอบความถูกต้องของข้อมูลความยินยอมสำหรับการอัพเดทฐานข้อมูล"""
    if not consent_data.get("contact_id") and not consent_data.get("contact_id"):
        frappe.log_error("Missing contact_id/parent", "Consent DB Update Validation Error")
        return False
    
    if not consent_data.get("consent_type"):
        frappe.log_error("Missing consent_type", "Consent DB Update Validation Error")
        return False
    
    return True

def validate_lookup_value(value, lookup_key):
    """ตรวจสอบค่าใน lookup"""
    # ตัวอย่างการตรวจสอบค่าใน lookup
    lookup_tables = {
        "GENDER": ["M", "F", "None"],
        "DataSourceCode": ["BA", "GGB", "GGA", "GGSUB", "HOSPITAL", "GGDB", "KUA", "BNF"],
        "NL_ANC_PLACE": ["GP", "PP", "GH", "PH", "CH", "UC", "UH", "OT"],
        "NL_BIRTH_PLAN": ["NB", "CS", "OT"],
        "NL_FORMULA": ["S26GC", "S26PE", "S26PC", "S26PR", "S26ME", "S26LF"],
        "NL_MOTHERSTAGE": ["M0", "M1", "M2", "M3", "M4", "M5", "MX", "BA"]
    }
    
    if lookup_key in lookup_tables:
        if value not in lookup_tables[lookup_key]:
            frappe.log_error(f"Invalid value for {lookup_key}: {value}, expected one of {lookup_tables[lookup_key]}", "Lookup Validation Error")
            return False
    
    return True

def validate_date_range(date_str, min_date=None, max_date=None, format="%Y-%m-%d"):
    """ตรวจสอบช่วงของวันที่"""
    try:
        date = datetime.strptime(date_str, format)
        
        if min_date and date < datetime.strptime(min_date, format):
            frappe.log_error(f"Date {date_str} is before minimum date {min_date}", "Date Range Validation Error")
            return False
            
        if max_date and date > datetime.strptime(max_date, format):
            frappe.log_error(f"Date {date_str} is after maximum date {max_date}", "Date Range Validation Error")
            return False
            
        return True
    except ValueError:
        frappe.log_error(f"Invalid date format: {date_str}", "Date Range Validation Error")
        return False 