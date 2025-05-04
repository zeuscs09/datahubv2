frappe.ui.form.on('ETL Main Profile', {
    refresh: function(frm) {
        // Add custom buttons or actions here
    },

    validate: function(frm) {
        // Additional client-side validation
        if (frm.doc.phone) {
            // Format phone number
            frm.doc.phone = frm.doc.phone.replace(/[^0-9]/g, '');
            if (frm.doc.phone.startsWith('+66')) {
                frm.doc.phone = '0' + frm.doc.phone.substring(3);
            }
        }
    },

    contact_id: function(frm) {
        // Auto-generate contact_id if empty
        if (!frm.doc.contact_id) {
            frm.set_value('contact_id', frappe.utils.get_random(10));
        }
    },

    gender: function(frm) {
        // Sync gender_sd with gender
        if (frm.doc.gender) {
            frm.set_value('gender_sd', frm.doc.gender);
        }
    }
}); 