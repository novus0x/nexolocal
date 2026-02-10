/*************** Modules ***************/
import express from 'express';

import { create_params } from '../../utils/params.js';
import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Main route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    
    const page = parseInt(req.query.page || "1", 10);
    const current_page = Math.max(page, 1);

    const type_of = req.query.type;
    const q = req.query.q;
    
    let suppliers = [];

    // Check permissions
    if (!permissions.includes("company.suppliers.read")) return res.redirect("/system-alert/403");

    // Request
    const params = create_params({ page: current_page, type_of: type_of, q: q })
    const response = await get_data(`/company/suppliers${params}`, {}, req);

    if (response.error) return res.redirect("/");

    const data = response.data;

    suppliers = data.suppliers

    // Render content
    return res.render("companies/suppliers/main", {
        suppliers,

        pagination: data.pagination,
        page: current_page,
        query: req.query
    });
});

/*************** Create Supplier - GET ***************/
router.get("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    
    // Check permissions
    if (!permissions.includes("company.suppliers.create")) return res.redirect("/system-alert/403");

    // Render content
    return res.render("companies/suppliers/create");
});

/*************** Create Supplier - POST ***************/
router.post("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const company_id = req.company_id;
    const permissions = req.permissions;

    let reason_name_v = "none";
    let document_v = "none";
    let email_v = "none";
    let phone_v = "none";
    let domain_v = "none";
    let address_v = "none";
    let supplier_type_v = "none";
    let is_active_v = "0";
    
    // Check permissions
    if (!permissions.includes("company.suppliers.create")) return res.redirect("/system-alert/403");

    // Body
    const { name, reason_name, document, email, phone, domain, address, supplier_type, is_active } = req.body;

    if (reason_name) reason_name_v = reason_name;
    if (document) document_v = document;
    if (email) email_v = email;
    if (phone) phone_v = phone;
    if (domain) domain_v = domain;
    if (address) address_v = address;
    if (supplier_type) supplier_type_v = supplier_type;
    if (is_active == "on") is_active_v = "1";

    const response = await send_data("/company/suppliers/create", {}, {
        name,

        reason_name: reason_name_v,
        document: document_v,
        email: email_v,
        phone: phone_v,
        domain: domain_v,
        address: address_v,
        supplier_type: supplier_type_v,
        is_active: is_active_v
    }, req);

    // Render content
    return res.redirect(`/companies/${company_id}/suppliers`)
});

/*************** Export ***************/
export default router
