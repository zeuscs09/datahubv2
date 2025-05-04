import frappe
from frappe.model.document import Document

class ETLChild(Document):
    pass
    # def validate(self):
    #     self.validate_required_fields()
    #     self.validate_data_types()
    #     self.set_default_values()
    #     self.validate_mother_exists()

    # def validate_required_fields(self):
    #     required_fields = ['cusid', 'motherid', 'fname', 'lname']
    #     for field in required_fields:
    #         if not self.get(field):
    #             frappe.throw(f"Field {field} is required")

    # def validate_data_types(self):
    #     # Validate birthdate format
    #     if self.birthdate and not isinstance(self.birthdate, str):
    #         frappe.throw("Invalid birthdate format")

    # def set_default_values(self):
    #     if not self.gender:
    #         self.gender = 'None'
    #     if not self.flag_complete:
    #         self.flag_complete = 'C'
    #     if not self.flag_active:
    #         self.flag_active = '1'
    #     if not self.signature:
    #         self.signature = 'N'
    #     if not self.createid:
    #         self.createid = '0'
    #     if not self.updateid:
    #         self.updateid = '0'
    #     if not self.born_place_id:
    #         self.born_place_id = 0
    #     if not self.born_place_type:
    #         self.born_place_type = '-'
    #     if not self.birth_plan:
    #         self.birth_plan = '-'
    #     if not self.mother_prod_id:
    #         self.mother_prod_id = 0
    #     if not self.current_mother_prod_id:
    #         self.current_mother_prod_id = 0

    # def validate_mother_exists(self):
    #     if self.motherid:
    #         if not frappe.db.exists("ETL Main Profile", self.motherid):
    #             frappe.throw(f"Mother ID {self.motherid} does not exist")

    # def before_save(self):
    #     self.updatedate = frappe.utils.now()
    #     if not self.createdate:
    #         self.createdate = frappe.utils.now()
    #     if not self.receivedate:
    #         self.receivedate = frappe.utils.now()

    # def after_insert(self):
    #     self.update_mother_child_info()

    # def update_mother_child_info(self):
    #     # Update child info in mother's record
    #     mother = frappe.get_doc("ETL Main Profile", self.motherid)
    #     mother.gg_hospital = self.gg_hospital
    #     mother.gg_child_delivery_type = self.gg_child_delivery_type
    #     mother.gg_milk_currently_consuming = self.gg_milk_currently_consuming
    #     mother.child_birthdatereliability = self.child_birthdatereliability
    #     mother.save() 