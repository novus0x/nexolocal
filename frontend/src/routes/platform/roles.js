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
    if (!permissions.includes("platform.roles.read")) return res.redirect("/system-alert/403");

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
    if (!permissions.includes("platform.roles.create")) return res.redirect("/system-alert/403");

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

    let errors = [];

    let hidden_v = "0";
    let permissions_data_v = [];
    let description_s = "No hay descripción";

    // Check permissions
    if (!permissions.includes("platform.roles.create")) return res.redirect("/system-alert/403");

    // Get POST data
    const { permissions_data, role_name, description, hidden } = req.body;

    // Correction
    if (description) description_s = description;

    if (hidden == "on") hidden_v = "1";

    if (typeof(permissions_data) == "string") permissions_data_v = [permissions_data]
    else permissions_data_v = permissions_data

    const response = await send_data("/platform/roles/create", {}, {
        role_name,
        
        permissions: permissions_data_v,
        description: description_s,
        hidden: hidden_v
    }, req);

    if (response.error) {
        let permissions_data_v = []

        if (response.details.length <= 0) errors = [response.message];
        else errors = response.details;

        const response2 = await get_data("/platform/roles/get-permissions", {}, req);

        if (response2.data.permissions) {
            permissions_data_v = response.data.permissions
        }

        return res.render("platform/roles/create", {
            permissions_data: permissions_data_v
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
    if (!permissions.includes("platform.roles.update")) return res.redirect("/system-alert/403");

    // Get Structure
    const response = await get_data(`/platform/roles/get/${role_id}`, {}, req);

    if (response.error) {
        return res.redirect("/platform/roles");
    }

    permissions_data = response.data.permissions
    permissions_selected_data = response.data.permissions_selected

    // Render content
    return res.render("platform/roles/update", {
        role_id: role_id, 
        permissions_data, 
        permissions_selected_data
    });
});

/*************** Edit Role - PUT ***************/
router.put("/update/:role_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const role_id = req.params.role_id;

    let hidden_v = "0";
    let description_s = "No hay descripción";
    let permissions_data_v = [];

    // Check permissions
    if (!permissions.includes("platform.roles.update")) return res.redirect("/system-alert/403");

    // Get POST data
    const { permissions_data, role_name, description, hidden } = req.body;

    if (typeof(permissions_data) == "string") permissions_data_v = [permissions_data]
    else permissions_data_v = permissions_data

    // Correction
    if (description) description_s = description;

    if (hidden == "on") hidden_v = "1";

    // Operations
    const response = await send_data(`/platform/roles/update/${role_id}`, {}, {
        role_name, 

        permissions: permissions_data_v,
        description: description_s,
        hidden: hidden_v
    }, req);

    if (response.error) {
        const response2 = await get_data(`/platform/roles/get/${role_id}`, {}, req);

        const permissions_data = response2.data.permissions;
        const permissions_selected_data = response2.data.permissions_selected;

        if (response2.error) {
            return res.redirect("/platform/roles");
        }

        return res.render("platform/roles/update", {
            errors: [response.message], 
            permissions_data, permissions_selected_data
        });
    }

    // Render content
    return res.redirect(`/platform/roles/update/${role_id}`);
});

/*************** Export ***************/
export default router
