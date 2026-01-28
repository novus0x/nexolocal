/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';
import { svg_generator } from '../../utils/generator.js';
import { create_params } from '../../utils/params.js';
import { num_to_string } from '../../utils/convert.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Sales Route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.sales.read")) {
        if (permissions.includes("company.sales.create")) return res.redirect(`/companies/${company_id}/sales/create`)
        
        return res.redirect("/");
    }

    const response = await get_data("/company/sales", {}, req);

    if (response.error) {
        return res.redirect("/");
    }

    const data = response.data;

    const sales = data.sales;

    // Render content
    return res.render("companies/sales/main", {
        sales: sales
    });
});

/*************** Check Receipt - Sales ***************/
router.get("/check/:sale_id", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const sale_id = req.params.sale_id;
 
    // Check permissions
    if (!permissions.includes("company.sales.read")) return res.redirect("/");

    const response = await get_data(`/company/sales/check_sale/${sale_id}`, {}, req)

    if (response.error) {
        return res.redirect("/");
    }

    const data = response.data;
    const qrcode = await svg_generator("nexolocal.floua.app/check-ticket"); // data.sale.id
    const string_value = num_to_string(data.sale.total);

    // Render content
    return res.render("companies/sales/documents/internal-ticket", {
        company: data.company,
        sale: data.sale,
        qrcode, string_value
    });
});

/*************** New Sale Route ***************/
router.get("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    // Render content
    return res.render("companies/sales/create", {});
});

/*************** Check Sale ***************/
router.get("/create/success/:sale_id", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const sale_id = req.params.sale_id;
    const company_id = req.company_id;
 
    // Check permissions
    if (!permissions.includes("company.sales.create")) return res.redirect("/");

    const response = await get_data(`/company/sales/check_sale/${sale_id}`, {}, req)

    if (response.error) {
        return res.redirect("/");
    }

    const data = response.data;
    const qrcode = await svg_generator(data.sale.id);
    const string_value = num_to_string(data.sale.total);

    // Render content
    return res.render("companies/sales/documents/ticket-to-print", {
        company: data.company,
        sale: data.sale,
        qrcode, string_value
    });
});

/*************** Check Sale ***************/
router.get("/reports", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    const page = parseInt(req.query.page || "1", 10);
    const current_page = Math.max(page, 1);
    const q = req.query.q;
 
    // Check permissions
    if (!permissions.includes("company.sales.read")) return res.redirect("/");

    const params = create_params({page: current_page, q: q});
    const response = await get_data(`/company/sales/reports${params}`, {}, req)

    if (response.error) {
        return res.redirect("/");
    }

    const data = response.data;

    // Render content
    return res.render("companies/sales/reports", {
        sales: data.sales,

        page: current_page,
        pagination: data.pagination,
        query: req.query
    });
});


/*************** Export ***************/
export default router
