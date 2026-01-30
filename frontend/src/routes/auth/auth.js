/*************** Modules ***************/
import express from 'express';

import settings from '../../settings.js';

import { send_data } from '../../utils/api.js';
import { require_auth, already_login } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

const oauth_providers = {
    google: settings.google_client_id
}

/*************** Render Authentication ***************/
router.get("/", already_login, (req, res) => {
    return res.render("auth/login", {
        oauth: oauth_providers
    });
});

/*************** Login - POST ***************/
router.post("/login", async (req, res) => {
    // Variables
    let expires = "0";

    // Get POST data
    const { email, password, expire } = req.body;

    if (expire) expires = "1";

    const response = await send_data("/auth/login", {}, {
        email, password, expires
    });

    // Error
    if (response.error) {
        // Details
        if (response.details.length > 0) {
            return res.render("auth/login", {
                errors: response.details,
                email, expire,

                oauth: oauth_providers
            })
        }

        // Message
        return res.render("auth/login", {
            errors: [response.message],
            email, expire,

            oauth: oauth_providers
        })
    }

    const cookie_value = response.data.cookie_value;
    if (cookie_value) res.setHeader("Set-Cookie", cookie_value);
    return res.redirect("/");
});

/*************** Register - POST ***************/
router.post("/register", async (req, res) => {
    // Get POST data
    const { username, fullname, email, password, confirm_password, birth } = req.body;
    
    // Send request
    const response = await send_data("/auth/register", {}, {
        username, fullname, email, password, confirm_password, birth
    });

    // Error
    if (response.error) {
        // Details
        if (response.details.length > 0) {
            return res.render("auth/register", {
                errors: response.details,
                username, fullname, email, birth,

                oauth: oauth_providers
            })
        }

        // Message
        return res.render("auth/register", {
            errors: [response.message],
            username, fullname, email, birth,

            oauth: oauth_providers
        })
    }

    return res.redirect("/auth");
});

/*************** Forgot Password - POST ***************/
router.post("/forgot-password", (req, res) => {
    const { email } = req.body;
    console.log(email)
    res.json("ok")
});

/*************** Logout - GET ***************/
router.get("/logout", require_auth, async (req, res) => {
    // Send logout request
    const response = await send_data("/auth/logout", {}, {}, req);
    const cookie_value = response.data.cookie_value;

    if (cookie_value) res.setHeader("Set-Cookie", cookie_value);
    res.clearCookie("company_id");

    res.redirect("/");
});

/*************** Export ***************/
export default router
