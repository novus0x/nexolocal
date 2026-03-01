/*************** Modules ***************/
import express from 'express';

import { send_data } from '../../../utils/api.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Flow - Payments ***************/
router.post("/flow", async (req, res) => {
    // Variables
    const company_id = req.query.company_id || "no_data";

    // Body
    const { token } = req.body;

    // Request
    const response = await send_data("/general/billing/validate", {}, {
        token, company_id
    }, req);

    return res.send("ok");
});

/*************** Export ***************/
export default router;
