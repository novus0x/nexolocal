/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Change Password ***************/
router.post("/settings/update_password", require_auth, async (req, res) => {
    // Variables
    let errors = [];

    // Get body
    const { current_password, new_password, confirm_new_password } = req.body;

    const response = await send_data("/users/update-password", {}, {
        current_password, new_password, confirm_new_password
    }, req)

    if (response.error) {
        if (response.details.length > 0) errors = response.details;
        else errors = [response.message];

        return res.json({
            error: true,
            errors: errors
        })
    }

    // Send Data
    return res.json({
        error: false,
        message: response.message
    });
});

/*************** Export ***************/
export default router
