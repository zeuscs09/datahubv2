frappe.ui.form.on('ETL Consent', {
    refresh: function(frm) {
        // Add custom buttons or actions here
    },

    validate: function(frm) {
        // Additional client-side validation
    },

    consent_id: function(frm) {
        // Auto-generate consent_id if empty
        if (!frm.doc.consent_id) {
            frm.set_value('consent_id', frappe.utils.get_random(10));
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

    consent_type: function(frm) {
        // Update fields based on consent type
        if (frm.doc.consent_type === 'MARKETING') {
            frm.set_value('is_consented', 'No');
            frm.set_value('marketing_subscribed_date', null);
            frm.set_value('marketing_subscribed_version', null);
        }
    },

    is_consented: function(frm) {
        // Update marketing subscribed date when consent is given
        if (frm.doc.is_consented === 'Yes' && frm.doc.consent_type === 'MARKETING') {
            frm.set_value('marketing_subscribed_date', frappe.datetime.now_datetime());
        }
    }
}); 