/*************** Modules ***************/
import express from 'express';

import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/settings", require_auth, async (req, res) => {
    // Render content
    return res.render("users/settings", {});
});

/*************** Export ***************/
export default router
