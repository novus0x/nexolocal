/*************** Modules ***************/
import path from 'path';
import { fileURLToPath } from 'url';

import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, no_permissions } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/*************** Main route ***************/
router.get("/", async (req, res) => {
    // Variables
    let plans = [];

    // Get Plans
    const response = await get_data("/general", {}, req);

    if (response.error == false) {
        plans = response.data.plans;
    }

    // Render content
    return res.render("general/main", {
        plans
    });
});

/*************** Legal route ***************/
router.get("/legal/terms", async (req, res) => {
    res.type("text/plain");
    return res.sendFile(
        path.join(__dirname, "../../public/legal/terms.txt")
    )
});

/*************** Export ***************/
export default router;
