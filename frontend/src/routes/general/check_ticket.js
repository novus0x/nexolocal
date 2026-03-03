/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/check-ticket", async (req, res) => {
    // Variables
    const query = (req.query.q || "").trim();
    let ticket = null;
    let error_message = null;

    // Actions
    if (query) {
        const response = await get_data(`/general/check-ticket?q=${encodeURIComponent(query)}`, {}, req);

        if (response.error) error_message = response.message || "No se encontro el comprobante.";
        else ticket = {
            company: response.data.company,
            sale: response.data.sale
        };
    }

    // Render content
    return res.render("general/check_ticket", {
        query,
        ticket,
        error_message
    });
});

/*************** Export ***************/
export default router;
