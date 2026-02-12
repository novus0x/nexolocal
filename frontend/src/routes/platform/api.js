/*************** Modules ***************/
import express from 'express';

import { create_params } from '../../utils/params.js';
import { get_data, send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Get Tickets ***************/
router.get("/support/tickets", require_auth, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    if (!permissions.includes("platform.support.tickets.read") && !permissions.includes("platform.support.tickets.manage")) return res.redirect("/system-alert/403");

    // Params
    const { q, priority, category, page, limit } = req.query;

    const params = create_params({
        q, priority, category, page, limit
    });

    const response = await get_data(`/platform/support/tickets${params}`, {}, req);

    // Fix err
    if (response.error) {
        return res.json({
            success: false,
            message: response.message,
            errors: response.details
        });
    }

    const data = response.data

    return res.json({
        success: true,
        tickets: data.tickets,
        pagination: data.pagination
    });
});

/*************** Create new Response ***************/
router.post("/support/tickets/response/create", require_auth, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let internal_v = "0";

    if (!permissions.includes("platform.support.tickets.response") && !permissions.includes("platform.support.tickets.manage")) return res.redirect("/system-alert/403");

    // Body
    const { ticket_id, description, internal } = req.body;

    if (internal) internal_v = "1";

    // Request
    const response = await send_data(`/platform/support/tickets/${ticket_id}/response/create`, {}, {
        description, 

        internal: internal_v
    }, req);

    // Fix err
    if (response.error) {
        return res.json({
            success: false,
            message: response.message,
            errors: response.details
        });
    }

    return res.json({
        success: true,
    });
});

/*************** Export ***************/
export default router
