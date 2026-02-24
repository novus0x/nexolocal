/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../../utils/api.js';
import { require_auth } from '../../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Dashboard ***************/
router.get("/", require_auth, async (req, res) => {
    // Variables

    // Get Data
    const response = await get_data("/general/dashboard", {}, req);

    if (response.error) return res.redirect("/");

    const data = response.data;

    // Render content
    return res.render("general/private/dashboard", {
        companies_q: data.companies_q,
        companies: data.companies
    });
});

/*************** Export ***************/
export default router;
