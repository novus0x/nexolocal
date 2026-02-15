/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Settings Route - GET ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.settings.read")) return res.redirect("/system-alert/403");

    // Request Data
    const response = await get_data("/company/settings", {}, req);

    if (response.error) return res.redirect("/platform");

    const data = response.data.information;
    console.log(data)

    // Render content
    return res.render("companies/settings/main", {
        company: data.company
    });
});

/*************** Settings Route - PUT ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.settings.update")) return res.redirect("/system-alert/403");

    // Request Data
    const response = await get_data("/company/settings", {}, req);

    if (response.error) return res.redirect("/platform");

    const data = response.data.information;
    console.log(data)

    // Render content
    return res.render("companies/settings/main", {
        company: data.company,
        plan: data.plan
    });
});

/*************** Export ***************/
export default router
