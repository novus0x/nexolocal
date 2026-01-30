/*************** Modules ***************/
import express from 'express';

import { send_data } from '../../utils/api.js';
import { require_auth } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Google Oauth ***************/
router.get('/google', async (req, res) => {
    const code = req.query.code;

    if (!code) {
        return res.status(400).send('No se recibió el código de Google');
    }

    const response = await send_data("/oauth/google", {}, {
        code
    }, req)

    if (response.error) {
        // Message
        return res.render("auth/login", {
            errors: [response.message],

            oauth: oauth_providers
        })
    }
    
    const cookie_value = response.data.cookie_value;
    if (cookie_value) res.setHeader("Set-Cookie", cookie_value);

    return res.redirect("/");
});

/*************** Export ***************/
export default router
