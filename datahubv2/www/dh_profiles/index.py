import frappe
from frappe import _

def get_context(context):
    # ดึงรายการโปรไฟล์คุณแม่ทั้งหมด
    profiles = frappe.get_all(
        'ETL Main Profile',
        fields=[
            'name', 'contact_id', 'first_name', 'last_name', 
            'phone', 'email', 'is_consented'
        ],
        order_by='date_registration desc'
    )
    
    # ดึงจำนวนบุตรสำหรับแต่ละคุณแม่
    for profile in profiles:
        children_count = frappe.db.count(
            'ETL Child',
            filters={'motherid': profile.name}
        )
        profile.children_count = children_count
    
    context.profiles = profiles
    context.title = _("รายการข้อมูลคุณแม่")
    
    return context 