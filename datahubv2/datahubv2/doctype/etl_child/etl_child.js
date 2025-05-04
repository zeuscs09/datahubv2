frappe.ui.form.on('ETL Child', {
    refresh: function(frm) {
        // Add custom buttons or actions here
    },

    validate: function(frm) {
        // Additional client-side validation
    },

    cusid: function(frm) {
        // Auto-generate cusid if empty
        if (!frm.doc.cusid) {
            frm.set_value('cusid', frappe.utils.get_random(10));
        }
    },

    motherid: function(frm) {
        // Fetch mother's information when motherid is selected
        if (frm.doc.motherid) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'ETL Main Profile',
                    name: frm.doc.motherid
                },
                callback: function(r) {
                    if (r.message) {
                        // Update fields based on mother's information
                        frm.set_value('mother_stage', r.message.mother_stage);
                    }
                }
            });
        }
    },

    birthdate: function(frm) {
        // Validate birthdate
        if (frm.doc.birthdate) {
            let birthdate = new Date(frm.doc.birthdate);
            let today = new Date();
            if (birthdate > today) {
                frappe.throw("Birth date cannot be in the future");
            }
        }
    }
}); 