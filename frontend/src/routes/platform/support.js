/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Support Main Route***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("platform.support.read")) return res.redirect("/system-alert/403");

    // Render content
    return res.render("platform/support/main", {
    });
});

/*************** Support ***************/
router.get("/tickets/:ticket_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    const ticket_id = req.params.ticket_id;

    // Check permissions
    if (!permissions.includes("platform.support.tickets.read") && !permissions.includes("platform.support.tickets.manage")) return res.redirect("/system-alert/403");

    // Request
    const response = await get_data(`/platform/support/tickets/get/${ticket_id}`, {}, req);

    if (response.error) return res.redirect("/platform/support/tickets");

    const data = response.data;

    const ticket = data.ticket;

    // Render content
    return res.render("platform/support/read", {
        ticket 
    });
});

/*************** Export ***************/
export default router
