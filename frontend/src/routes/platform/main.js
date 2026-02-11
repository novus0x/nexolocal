/*************** Modules ***************/
import express from 'express';

import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("platform.dashboard.read")) return res.redirect("/dashboard");

    // Render content
    return res.render("platform/dashboard", {});
});

/*************** Export ***************/
export default router
