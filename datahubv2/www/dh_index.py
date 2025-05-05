import frappe
from frappe import _

def get_context(context):
    # ข้อมูลสถิติ
    stats = {
        'profiles_count': frappe.db.count('ETL Main Profile'),
        'children_count': frappe.db.count('ETL Child'),
        'campaigns_count': frappe.db.count('ETL Campaign'),
        'active_consents': frappe.db.count('ETL Consent', {'is_consented': 'Yes'})
    }
    
    context.stats = stats
    context.title = _("DataHub | ระบบจัดการข้อมูลคุณแม่และเด็ก")
    
    return context 