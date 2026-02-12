/*************** Modules ***************/
import express, { response } from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Support Main Route ***************/
router.get("/", require_auth, async (req, res) => {
    // Variables

    // Render content
    return res.render("general/support/main", {});
});

/*************** Tickets Support Create - GET ***************/
router.get("/tickets/create", require_auth, async (req, res) => {
    // Variables

    // Render content
    return res.render("general/support/tickets/create", {});
});

/*************** Tickets ***************/
router.get("/tickets", require_auth, async (req, res) => {
    // Variables

    // Request
    const response = await get_data("/general/support/tickets", {}, req);

    if (response.error) return res.redirect("/platform");

    const data = response.data;

    const tickets = data.tickets;

    // Render content
    return res.render("general/support/tickets/main", {
        tickets
    });
});

/*************** Tickets ***************/
router.get("/tickets/:ticket_id", require_auth, async (req, res) => {
    // Variables
    const ticket_id = req.params.ticket_id;

    // Request
    const response = await get_data(`/general/support/tickets/get/${ticket_id}`, {}, req);

    const data = response.data;
    const ticket = data.ticket;

    // Render content
    return res.render("general/support/tickets/read", {
        ticket
    });
});

/*************** Export ***************/
export default router;
