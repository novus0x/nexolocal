/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Get Companies ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let companies = [];

    // Check permissions
    if (!permissions.includes("platform.companies.read")) return res.redirect("/");

    const response = await get_data("/platform/companies", {}, req);

    if (response.error) {
        return res.redirect("/platform/companies");
    }

    const data = response.data;

    if (data.companies) companies = data.companies;

    // Render content
    return res.render("platform/companies/main", {
        companies: companies
    });
});

/*************** Create Company - Get ***************/
router.get("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let roles = [];

    // Check permissions
    if (!permissions.includes("platform.companies.create")) return res.redirect("/");
    
    const response = await get_data("/platform/companies/get_roles", {}, req);

    if (response.error) {
        return res.redirect("/platform/companies");
    }

    if (response.data.roles) roles = response.data.roles;

    // Render content
    return res.render("platform/companies/create", {
        roles: roles
    });
});

/*************** Create Company - POST ***************/
router.post("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let notes_s = "Empty";

    // Check permissions
    if (!permissions.includes("platform.companies.create")) return res.redirect("/");

    const { name, email, notes, role_id } = req.body;

    if (notes) notes_s = notes;

    const response = await send_data("/platform/companies/create", {}, {
        name, email, role_id, notes: notes_s
    }, req);

    if (response.error) {
        // Extra Variables
        let roles = [];

        const response2 = await get_data("/platform/companies/get_roles", {}, req);

        if (response2.error) {
            return res.redirect("/platform/companies");
        }

        if (response2.data.roles) roles = response2.data.roles;

        return res.render("platform/companies/create", {
            errors: [response.message],
            roles: roles,
            name, 
            email, 
            role_id, 
            notes: notes_s
        });
    }

    // Render content
    return res.redirect(`/platform/companies/view/${response.data.company_id}`);
});

/*************** Export ***************/
export default router
