frappe.ui.form.on('ETL Campaign', {
    refresh: function(frm) {
        // Add custom buttons or actions here
    },

    validate: function(frm) {
        // Additional client-side validation
    },

    campaign_id: function(frm) {
        // Auto-generate campaign_id if empty
        if (!frm.doc.campaign_id) {
            frm.set_value('campaign_id', frappe.utils.get_random(10));
        }
    },

    parent: function(frm) {
        // Fetch parent's information when parent is selected
        if (frm.doc.parent) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'ETL Main Profile',
                    name: frm.doc.parent
                },
                callback: function(r) {
                    if (r.message) {
                        // Update fields based on parent's information
                    }
                }
            });
        }
    },

    campaign_start_date: function(frm) {
        // Validate campaign dates
        if (frm.doc.campaign_start_date && frm.doc.campaign_end_date) {
            if (frm.doc.campaign_start_date > frm.doc.campaign_end_date) {
                frappe.throw("Campaign start date cannot be after end date");
            }
        }
    },

    campaign_end_date: function(frm) {
        // Validate campaign dates
        if (frm.doc.campaign_start_date && frm.doc.campaign_end_date) {
            if (frm.doc.campaign_start_date > frm.doc.campaign_end_date) {
                frappe.throw("Campaign start date cannot be after end date");
            }
        }
    }
}); 