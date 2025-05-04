import frappe
from frappe.model.document import Document
import json
from datetime import datetime

class ETLSyncLog(Document):
    def validate(self):
        self.validate_required_fields()
        self.validate_dates()
        self.set_default_values()
        self.validate_records_count()
        self.validate_error_log()
        self.validate_raw_data()

    def validate_required_fields(self):
        if not self.sync_id:
            frappe.throw("Sync ID is required")
        if not self.sync_type:
            frappe.throw("Sync Type is required")
        if not self.sync_date:
            frappe.throw("Sync Date is required")

    def validate_dates(self):
        if self.sync_date and self.sync_date > frappe.utils.now():
            frappe.throw("Sync Date cannot be in the future")

    def set_default_values(self):
        if not self.status:
            self.status = "Pending"
        if not self.total_records:
            self.total_records = 0
        if not self.processed_records:
            self.processed_records = 0

    def validate_records_count(self):
        if self.processed_records > self.total_records:
            frappe.throw("Processed Records cannot be greater than Total Records")
        if self.total_records < 0:
            frappe.throw("Total Records cannot be negative")
        if self.processed_records < 0:
            frappe.throw("Processed Records cannot be negative")
        if self.success_records < 0:
            frappe.throw("Success Records cannot be negative")
        if self.failed_records < 0:
            frappe.throw("Failed Records cannot be negative")
        
        if self.success_records + self.failed_records > self.processed_records:
            frappe.throw("Sum of Success and Failed Records cannot exceed Processed Records")

    def validate_error_log(self):
        if self.error_log:
            try:
                json.loads(self.error_log)
            except json.JSONDecodeError:
                frappe.throw("Error Log must be valid JSON")

    def validate_raw_data(self):
        if self.raw_data:
            try:
                json.loads(self.raw_data)
            except json.JSONDecodeError:
                frappe.throw("Raw Data must be valid JSON")

    def before_save(self):
        self.updatedate = frappe.utils.now()
        if self.is_new():
            self.createdate = frappe.utils.now()
            self.receivedate = frappe.utils.now()

    def after_insert(self):
        self.update_sync_status()

    def update_sync_status(self):
        if self.status == "Completed":
            frappe.msgprint("Sync completed successfully")
        elif self.status == "Failed":
            frappe.msgprint("Sync failed. Please check error log for details")

    def update_progress(self, processed=0, success=0, failed=0, error=None):
        """Update sync progress"""
        self.processed_records = processed
        self.success_records = success
        self.failed_records = failed
        
        if error:
            self.error_log = json.dumps(error, indent=2)
            self.status = "Failed"
        else:
            if processed == self.total_records:
                self.status = "Completed"
            else:
                self.status = "Processing"
        
        self.save()
        frappe.db.commit()

    @frappe.whitelist()
    def start_sync(self, total_records):
        """Start a new sync process"""
        self.total_records = total_records
        self.processed_records = 0
        self.success_records = 0
        self.failed_records = 0
        self.status = "Processing"
        self.save()
        frappe.db.commit()

    @frappe.whitelist()
    def log_error(self, error_data):
        """Log error details"""
        try:
            error_json = json.loads(error_data)
            self.error_log = json.dumps(error_json, indent=2)
            self.status = "Failed"
            self.save()
            frappe.db.commit()
        except json.JSONDecodeError:
            frappe.throw("Invalid error data format")

    @frappe.whitelist()
    def get_progress(self):
        """Get current sync progress"""
        return {
            "total": self.total_records,
            "processed": self.processed_records,
            "success": self.success_records,
            "failed": self.failed_records,
            "status": self.status
        } 