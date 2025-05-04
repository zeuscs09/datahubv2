import frappe
from frappe.model.document import Document

class ETLCampaign(Document):
    pass
    # def validate(self):
    #     self.validate_required_fields()
    #     self.validate_dates()
    #     self.set_default_values()
    #     self.validate_parent_exists()

    # def validate_required_fields(self):
    #     required_fields = ['campaign_id', 'parent', 'campaign_name']
    #     for field in required_fields:
    #         if not self.get(field):
    #             frappe.throw(f"Field {field} is required")

    # def validate_dates(self):
    #     if self.campaign_start_date and self.campaign_end_date:
    #         if self.campaign_start_date > self.campaign_end_date:
    #             frappe.throw("Campaign start date cannot be after end date")

    # def set_default_values(self):
    #     if not self.campaign_status:
    #         self.campaign_status = 'Active'
    #     if not self.create_date:
    #         self.create_date = frappe.utils.now()
    #     if not self.last_update_date:
    #         self.last_update_date = frappe.utils.now()
    #     if not self.date_registration:
    #         self.date_registration = frappe.utils.now()
    #     if not self.last_updated:
    #         self.last_updated = frappe.utils.now()

    # def validate_parent_exists(self):
    #     if self.parent:
    #         if not frappe.db.exists("ETL Main Profile", self.parent):
    #             frappe.throw(f"Parent {self.parent} does not exist")

    # def before_save(self):
    #     self.last_update_date = frappe.utils.now()
    #     self.last_updated = frappe.utils.now()

    # def after_insert(self):
    #     self.update_parent_campaign_info()

    # def update_parent_campaign_info(self):
    #     # Update campaign info in parent's record
    #     parent = frappe.get_doc("ETL Main Profile", self.parent)
    #     parent.save() 