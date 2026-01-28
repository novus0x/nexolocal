/*************** Modules ***************/
import express from 'express';

import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, platform_mod, (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Render content
    return res.render("platform/dashboard", {
    });
});

/*************** Export ***************/
export default router
