/*************** Modules ***************/
import express from 'express';

import { send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Open Ticket ***************/
router.post("/support/tickets/create", require_auth, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let errors = [];

    // Data
    const { category, priority, title, description } = req.body;

    // Send Data
    const response = await send_data("/general/support/tickets/create", {}, {
        category, priority, title, description
    }, req);

    if (response.error) {
        if (response.details.length > 0) errors = response.details;
        else errors = [response.message];

        return res.json({
            success: true,
            errors: errors
        })
    }

    const data = response.data;

    return res.json({
        success: true,
        code: data.ticket_code
    })
});

/*************** Create new Response ***************/
router.post("/support/tickets/response/create", require_auth, async (req, res) => {
    // Body
    const { ticket_id, description } = req.body;

    // Request
    const response = await send_data(`/general/support/tickets/${ticket_id}/response/create`, {}, {
        description, 
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
