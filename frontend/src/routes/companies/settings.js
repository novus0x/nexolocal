/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Sales Route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.settings.read")) return res.redirect("/system-alert/403");


    // Render content
    return res.render("companies/settings/main", {});
});

/*************** Export ***************/
export default router
