/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Get Analytics ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let companies = [];

    // Check permissions
    if (!permissions.includes("platform.analytics.read")) return res.redirect("/");

    // Render content
    return res.render("platform/analytics/main", {});
});

/*************** Export ***************/
export default router
