import frappe

def get_context(context):
    # ดึงข้อมูล Contact ID จาก URL หรือใช้ค่าเริ่มต้น
    contact_id = frappe.form_dict.get('contact_id')
    
    if not contact_id:
        frappe.local.flags.redirect_location = '/404'
        raise frappe.Redirect
    
    # ดึงข้อมูลโปรไฟล์หลัก
    try:
        profile = frappe.get_doc('ETL Main Profile', contact_id)
        context.doc = profile
    except frappe.DoesNotExistError:
        frappe.local.flags.redirect_location = '/404'
        raise frappe.Redirect
    
    # ดึงข้อมูลเด็ก
    children = frappe.get_all(
        'ETL Child',
        filters={'motherid': contact_id},
        fields=['*']
    )
    context.children = children
    
    # ดึงข้อมูลแคมเปญ
    campaigns = frappe.get_all(
        'ETL Campaign',
        filters={'contact_id': contact_id},
        fields=['*']
    )
    context.campaigns = campaigns
    
    # ดึงข้อมูลการยินยอม
    consents = frappe.get_all(
        'ETL Consent',
        filters={'contact_id': contact_id},
        fields=['*'],
        order_by='consent_date desc'
    )
    context.consents = consents

    # ตั้งค่าหัวข้อเว็บเพจ
    full_name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
    context.title = f"ข้อมูลคุณแม่: {full_name}" if full_name else "ข้อมูลคุณแม่"
    
    return context 