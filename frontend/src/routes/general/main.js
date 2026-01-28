/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, no_permissions } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, no_permissions, (req, res) => {
    // Variables

    // Render content
    return res.render("general/dashboard", {});
});

/*************** Export ***************/
export default router;
