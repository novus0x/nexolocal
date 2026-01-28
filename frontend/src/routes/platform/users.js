/*************** Modules ***************/
import express from 'express';

import { get_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let users = [];

    // Check permissions
    if (!permissions.includes("platform.users.read")) return res.redirect("/");

    // Get Structure
    const response = await get_data("/platform/users/", {}, req);

    if (response.data.users) users = response.data.users;

    // Render content
    return res.render("platform/users/main", {
        users: users
    });
});

/*************** Export ***************/
export default router
