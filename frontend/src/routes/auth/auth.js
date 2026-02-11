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
router.get("/", already_login, async (req, res) => {
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
    return res.redirect("/platform");
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
router.post("/forgot-password", async (req, res) => {
    // Body
    const { email } = req.body;

    // Send Data
    const response = await send_data("/auth/forgot-password", {}, {
        email
    }, req)

    // Response
    return res.render("auth/reset_password_sent")
});

/*************** Recover - Get ***************/
router.get("/recover", async (req, res) => {
    // Variables
    const recover_id = req.query.id;

    if (!recover_id) return res.redirect("/");

    // Send Data
    const response = await send_data("/auth/recover-account-verify", {}, {
        recover_id
    }, req)

    if (response.error) return res.redirect("/");

    // Response
    return res.render("auth/recover", {
        recover_id
    })
});

/*************** Recover - Post ***************/
router.post("/recover", async (req, res) => {
    // Variables
    const recover_id = req.query.id;

    if (!recover_id) return res.redirect("/");

    // Body
    const { new_password, confirm_new_password } = req.body;

    // Send Data
    const response = await send_data("/auth/recover-account", {}, {
        recover_id, new_password, confirm_new_password
    }, req)

    // Error
    if (response.error) {
        // Details
        if (response.details.length > 0) {
            return res.render("auth/recover", {
                errors: response.details,
                recover_id
            })
        }

        // Message
        return res.render("auth/recover", {
            errors: [response.message],
            recover_id
        })
    }

    // Response
    return res.render("auth/recover_success");
});

/*************** Logout - GET ***************/
router.get("/logout", require_auth, async (req, res) => {
    // Send logout request
    const response = await send_data("/auth/logout", {}, {}, req);
    const cookie_value = response.data.cookie_value;

    if (cookie_value) res.setHeader("Set-Cookie", cookie_value);
    res.clearCookie("company_id");

    return res.redirect("/");
});

/*************** Export ***************/
export default router
