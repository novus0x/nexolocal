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

/*************** New Sale - Create ***************/
router.post("/sales/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let client_id_value = "null";

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const { client_id, payment_method, items } = req.body;

    if (client_id) client_id_value = client_id;    

    const response = await send_data("/company/sales/create", {}, {
        client_id: client_id_value,
        payment_method,
        items
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

/*************** Export ***************/
export default router
