/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Users ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let users = [];

    // Check permissions
    if (!permissions.includes("platform.users.read")) return res.redirect("/");

    // Get Structure
    const response = await get_data("/platform/users", {}, req);

    if (response.data.users) users = response.data.users;

    // Render content
    return res.render("platform/users/main", {
        users: users
    });
});

/*************** Get User ***************/
router.get("/read/:user_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const user_id = req.params.user_id;
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("platform.users.read")) return res.redirect("/");

    const response = await get_data(`/platform/users/get/${user_id}`, {}, req);

    if (response.error) return res.redirect("/");

    const data = response.data;

    // Render content
    return res.render("platform/users/read", {
        user_data: data.user,
        user_role: data.role
    });
});

/*************** Update User - GET ***************/
router.get("/update/:user_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const user_id = req.params.user_id;
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("platform.users.update")) return res.redirect("/");

    const response = await get_data(`/platform/users/update/${user_id}`, {}, req);

    if (response.error) return res.redirect("/");

    const data = response.data;

    // Render content
    return res.render("platform/users/update", {
        roles: data.roles,
        user_data: data.user,
        user_role: data.role
    });
});

/*************** Update User - GET ***************/
router.put("/update/:user_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const user_id = req.params.user_id;
    const permissions = req.permissions;
    
    const notifications = [];

    let email_v = "no_change";
    let status_v = "active";
    let role_v = "no_change";
    let phone_v = "no_phone";
    let description_v = "no_description";

    // Check permissions
    if (!permissions.includes("platform.users.update")) return res.redirect("/");

    // Content
    const { status, role, username, fullname, email, phone, description } = req.body;

    // if (email) email_v = email; // Disable
    if (status) status_v = status;
    if (role) role_v = role;
    if (phone) phone_v = phone;
    if (description) description_v = description;

    const response = await send_data(`/platform/users/update/${user_id}`, {}, {
        email: email_v,
        status: status_v,
        role: role_v,
        phone: phone_v,
        description: description_v,

        username, fullname
    }, req);

    const response2 = await get_data(`/platform/users/update/${user_id}`, {}, req);

    if (response.error) {
        let errors = [];

        const fall_data = response2.data;

        if (response.details.length <= 0) errors = [response.message];
        else errors = response.details;

        return res.render("platform/users/update", {
            errors,
            user_data: fall_data.user
        });
    }

    const data2 = response2.data;

    notifications.push({
        message: "Usuario Actualizado",
        type: "success"
    })

    // Render content
    return res.render("platform/users/update", {
        notifications, 

        roles: data2.roles,
        user_data: data2.user,
        user_role: data2.role
    });
});

/*************** Export ***************/
export default router
