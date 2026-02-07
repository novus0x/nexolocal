/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Main route ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let roles = [];

    // Check permissions
    if (!permissions.includes("platform.roles.read")) return res.redirect("/");

    // Get Structure
    const response = await get_data("/platform/roles", {}, req);

    if (response.data.roles) roles = response.data.roles;

    // Render content
    return res.render("platform/roles/main", {
        roles: roles
    });
});

/*************** Create Role - GET ***************/
router.get("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let permissions_data = [];

    // Check permissions
    if (!permissions.includes("platform.roles.create")) return res.redirect("/");

    // Get Structure
    const response = await get_data("/platform/roles/get-permissions", {}, req);

    if (response.data.permissions) {
        permissions_data = response.data.permissions
    }

    // Render content
    return res.render("platform/roles/create", {
        permissions_data: permissions_data
    });
});

/*************** Create Role - POST ***************/
router.post("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let description_s = "No hay descripción";

    // Check permissions
    if (!permissions.includes("platform.roles.create")) return res.redirect("/");

    // Get POST data
    const { permissions_data, role_name, description } = req.body;

    // Correction
    if (description) description_s = description;

    const response = await send_data("/platform/roles/create", {}, {
        permissions: permissions_data, role_name, description: description_s
    }, req);

    if (response.error) {
        return res.render("platform/roles/main", {
            errors: [response.message],
        });
    }

    const data = response.data;

    // Render content
    return res.redirect(`/platform/roles/view/${data.role_id}`);
});

/*************** Edit Role - GET ***************/
router.get("/update/:role_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const role_id = req.params.role_id;

    let permissions_data = [];
    let permissions_selected_data = {};

    // Check permissions
    if (!permissions.includes("platform.roles.update")) return res.redirect("/");

    // Get Structure
    const response = await get_data(`/platform/roles/get/${role_id}`, {}, req);

    if (response.error) {
        return res.redirect("/platform/roles");
    }

    permissions_data = response.data.permissions
    permissions_selected_data = response.data.permissions_selected

    // Render content
    return res.render("platform/roles/update", {
        role_id: role_id, permissions_data, permissions_selected_data
    });
});

/*************** Edit Role - PUT ***************/
router.put("/update/:role_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const role_id = req.params.role_id;

    let description_s = "No hay descripción";

    // Check permissions
    if (!permissions.includes("platform.roles.update")) return res.redirect("/");

    // Get POST data
    const { permissions_data, role_name, description } = req.body;

    // Correction
    if (description) description_s = description;

    // Operations
    const response = await send_data(`/platform/roles/update/${role_id}`, {}, {
        permissions: permissions_data, role_name, description: description_s
    }, req);

    if (response.error) {
        const response2 = await get_data(`/platform/roles/get/${role_id}`, {}, req);

        const permissions_data = response2.data.permissions;
        const permissions_selected_data = response2.data.permissions_selected;

        if (response2.error) {
            return res.redirect("/platform/roles");
        }

        return res.render("platform/roles/update", {
            errors: [response.message], permissions_data, permissions_selected_data
        });
    }

    // Render content
    return res.redirect(`/platform/roles/read/${role_id}`);
});

/*************** Export ***************/
export default router
