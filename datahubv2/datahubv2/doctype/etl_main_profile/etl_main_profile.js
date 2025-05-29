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

  
}); 