/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/check-ticket", async (req, res) => {
    // Variables

    // Render content
    return res.render("general/check_ticket", {});
});

/*************** Export ***************/
export default router;
