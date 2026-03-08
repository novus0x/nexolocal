/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Close Cash ***************/
router.post("/cash/close", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let errors = [];
    let amount_v = 0;
    let description_v = "No description";

    // Check permissions
    if (!permissions.includes("company.cash.close")) return res.redirect("/");

    const { amount, description } = req.body;
    
    if (amount) amount_v = amount;
    if (description) description_v = description;

    const response = await send_data("/company/cash/close", {}, {
        amount: amount_v,
        description: description_v
    }, req)

    if (response.error) {
        if (response.details.length <= 0) errors.push(response.message);
        else errors = response.details;

        return res.json({
            error: true,
            errors: errors
        })
    }

    const data = response.data;

    // Return data
    return res.json({
        error: false,
        invalid_description: data.invalid_description,
        difference: data.difference
    })
});

/*************** Sales Route ***************/
router.post("/sales/check_product_scan", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const { identifier } = req.body;

    if (!identifier) {
        return res.json({
            error: true,
        })
    }

    const response = await send_data("/company/sales/check_product_scan", {}, {
        identifier: identifier
    }, req);

    if (response.error) {
        return res.json({
            error: true,
            msg: response.message
        })
    }

    const data = response.data;

    // Render content
    return res.json({
        error: false,
        data: {
            product: data.product
        },
    })
});

/*************** Sale Check Product Search ***************/
router.post("/sales/check_product_search", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const { query } = req.body;

    if (!query) {
        return res.json({
            error: true,
        })
    }

    const response = await send_data("/company/sales/check_product_search", {}, {
        query: query
    }, req);

    if (response.error) {
        return res.json({
            error: true,
        })
    }

    const data = response.data;

    // Return data
    return res.json({
        error: false,
        data: {
            products: data.products
        },
    })
});

/*************** Sale Check Customer ***************/
router.post("/sales/check_customer", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const { email, phone, doc_type, doc_number } = req.body;

    const response = await send_data("/company/sales/check_customer", {}, {
        email,
        phone,
        doc_type,
        doc_number
    }, req);

    if (response.error) {
        return res.json({
            error: true,
            msg: response.message
        })
    }

    return res.json({
        error: false,
        data: {
            customer: response.data.customer
        }
    })
});

/*************** New Sale - Create ***************/
router.post("/sales/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let client_value = null;

    let send_sale_v = "0";
    let invoice_method_v = "3";

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const { client, payment_method, items, send_sale, invoice_method } = req.body;

    if (send_sale) send_sale_v = "1";

    if (invoice_method == "receipt") invoice_method_v = "3";
    else invoice_method_v = "1";

    if (client) client_value = client;

    const response = await send_data("/company/sales/create", {}, {
        payment_method,
        items,
        client: client_value,
        send_sale: send_sale_v,
        invoice_method: invoice_method_v
    }, req);

    if (response.error) {
        let errors = [];

        if (response.details.length <= 0) errors.push(response.message);
        else errors = response.details;

        return res.json({
            error: true,
            errors: errors
        })
    }

    // Return data
    return res.json({
        error: false,
        sale_id: response.data.sale_id
    })
});

/*************** Cash Flow - Get Data ***************/
router.get("/cash/flow/:type", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const type = req.params.type;

    const available_options = ["today", "7d", "30d", "6m", "12m"];

    // Check permissions
    if (!permissions.includes("company.sales.read")) return res.redirect("/");

    if (!available_options.includes(type)) return res.redirect("/");

    const response = await send_data("/company/sales/flow", {}, {
        type
    }, req);

    if (response.error) return res.redirect("/");

    const data = response.data;

    return res.json({
        error: false,
        data
    })
});

/*************** Validate Active Service ***************/
router.post("/active_services/validate", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const { active_service_id } = req.body;

    // Check permissions
    if (!permissions.includes("company.sales.create") && !permissions.includes("company.active_services.update")) {
        return res.redirect("/");
    }

    const response = await send_data(`/company/active_services/validate/${active_service_id}`, {}, {}, req);

    if (response.error) {
        return res.json({
            error: true,
            msg: response.message
        });
    }

    return res.json({
        error: false,
        data: {
            service: response.data.service,
            active_quantity: response.data.active_quantity
        }
    });
});

/*************** Link Active Service Customer ***************/
router.post("/active_services/link_customer", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const { active_service_id, name, email, phone, doc_type, doc_number } = req.body;

    // Check permissions
    if (!permissions.includes("company.sales.create") && !permissions.includes("company.active_services.update")) {
        return res.redirect("/");
    }

    const response = await send_data(`/company/active_services/link_customer/${active_service_id}`, {}, {
        name,
        email,
        phone,
        doc_type,
        doc_number
    }, req);

    if (response.error) {
        return res.json({
            error: true,
            msg: response.message
        });
    }

    return res.json({
        error: false,
        data: {
            service: response.data.service,
            active_quantity: response.data.active_quantity
        }
    });
});

/*************** Export ***************/
export default router
