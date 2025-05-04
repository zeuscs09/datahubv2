import frappe
from frappe.model.document import Document

class ETLMainProfile(Document):
    def validate(self):
        self.validate_required_fields()
        self.validate_data_types()
        self.set_default_values()

    def validate_required_fields(self):
        required_fields = ['contact_id', 'first_name', 'last_name']
        for field in required_fields:
            if not self.get(field):
                frappe.throw(f"Field {field} is required")

    def validate_data_types(self):
        # Validate phone number format
        if self.phone and not self.phone.isdigit():
            frappe.throw("Phone number must contain only digits")

        # Validate email format
        if self.email and '@' not in self.email:
            frappe.throw("Invalid email format")

        # Validate postal code format
        if self.postal_code and (not self.postal_code.isdigit() or len(self.postal_code) != 5):
            frappe.throw("Postal code must be 5 digits")

    def set_default_values(self):
        if not self.gender:
            self.gender = 'None'
        if not self.birth_date:
            self.birth_date = '2000-01-01'
        if not self.contact_source:
            self.contact_source = 'BA'
        if not self.status:
            self.status = '1'
        if not self.income:
            self.income = '0'

    def before_save(self):
        self.last_updated = frappe.utils.now()
        if not self.date_registration:
            self.date_registration = frappe.utils.now()

    def after_insert(self):
        self.create_related_records()

    def create_related_records(self):
        # Create related records in other doctypes if needed
        pass 