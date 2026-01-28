/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Invitations ***************/
router.get("/", require_auth, async (req, res) => {
    // Variables
    const response = await get_data("/general/invitations", {}, req);

    const invitations = response.data?.invitations;

    // Render content
    return res.render("general/invitations/main", {
        invitations: invitations
    });
});

router.get("/accept/:invitation_id", require_auth, async (req, res) => {
    // Variables
    const response = await send_data("/general/invitations/accept", {}, {
        invitation_id: req.params.invitation_id
    }, req);

    if (response.error) {
        const response2 = await get_data("/general/invitations", {}, req);

        const invitations = response2.data?.invitations;

        return res.render("general/invitations/main", {
            errors: [response.message],
            invitations: invitations
        })
    }

    // Render content
    return res.render("general/invitations/accepted", {})
});

router.get("/decline/:invitation_id", require_auth, async (req, res) => {
    // Variables

    // Render content
    return res.json(req.params.invitation_id);
});

/*************** Export ***************/
export default router;
