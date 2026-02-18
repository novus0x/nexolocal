/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Users ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let users = [];

    // Check permissions
    if (!permissions.includes("platform.plans.read")) return res.redirect("/system-alert/403");

    // Render content
    return res.render("platform/plans/main", {
    });
});

/*************** Export ***************/
export default router
