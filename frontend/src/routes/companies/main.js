/*************** Modules ***************/
import express from 'express';

import { require_auth, at_least_company } from '../../middlewares/auth.js';
import { get_data, send_data } from '../../utils/api.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const user = req.user;
    const permissions = req.permissions;
    const company_id = req.params.company_id;

    // Render content
    if (company_id) return res.redirect(`/companies/${company_id}`);

    return res.render("companies/dashboard", {
    });
});

router.get("/:company_id", require_auth, at_least_company, async (req, res) => {
    // Variables
    const user = req.user;
    const permissions = req.permissions;

    const company_id = req.params.company_id;

    // Check permissions
    if (!permissions.includes("company.read")) return res.redirect("/");

    const response = await get_data("/company/dashboard", {}, req);

    if (response.error) return res.redirect("/");

    const data = response.data;
    console.log(data)

    // Render content
    res.render("companies/dashboard", {
        company: data.company,
        products: data.products
    });
});

/*************** Export ***************/
export default router
