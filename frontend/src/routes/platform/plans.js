/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, platform_mod } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Plans ***************/
router.get("/", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    let users = [];

    // Check permissions
    if (!permissions.includes("platform.plans.read")) return res.redirect("/system-alert/403");

    // Get Plans
    const response = await get_data("/platform/plans", {}, req);

    if (response.error) return res.redirect("/platform");

    const data = response.data;

    // Render content
    return res.render("platform/plans/main", {
        plans: data.plans
    });
});

/*************** Create Plan - GET ***************/
router.get("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("platform.plans.create")) return res.redirect("/system-alert/403");

    // Get Roles
    const response = await get_data("/platform/plans/get_roles", {}, req);

    if (response.error) return res.redirect("/platform/plans");

    const data = response.data;

    // Render content
    return res.render("platform/plans/create", {
        roles: data.roles
    });
});

/*************** Create Plan - POST ***************/
router.post("/create", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let highlight_v = "0";
    let highlight_title_v = "none";
    let highlight_subtitle_v = "none";

    // Check permissions
    if (!permissions.includes("platform.plans.create")) return res.redirect("/system-alert/403");

    // Body
    const { name, price, description, highlight, highlight_title, highlight_subtitle, cycle, position, role_id } = req.body;

    // Check
    if (highlight == "on") highlight_v = "1";
    if (highlight_title) highlight_title_v = highlight_title;
    if (highlight_subtitle) highlight_subtitle_v = highlight_subtitle;

    // Send Request
    const response = await send_data("/platform/plans/create", {}, {
        name, price, description, cycle, position, role_id,
        
        highlight: highlight_v,
        highlight_title: highlight_title_v,
        highlight_subtitle: highlight_subtitle_v
    }, req);
    
    // Error
    if (response.error) {
        const response2 = await get_data("/platform/plans/get_roles", {}, req);

        if (response2.error) return res.redirect("/platform/plans");

        const data2 = response2.data;

        return res.render("platform/plans/create", {
            name, price, description, highlight, highlight_title, 
            highlight_subtitle,

            role_id: role_id,
            roles: data2.roles
        });
    }

    // Render content
    return res.redirect("/platform/plans");
});

/*************** Update Plan - GET ***************/
router.get("/update/:plan_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const plan_id = req.params.plan_id;

    // Check permissions
    if (!permissions.includes("platform.plans.update")) return res.redirect("/system-alert/403");

    // Get Roles
    const response = await get_data("/platform/plans/get_roles", {}, req);

    if (response.error) return res.redirect("/platform/plans");

    // Get Plan
    const response2 = await get_data(`/platform/plans/get/${plan_id}`, {}, req);

    const data = response.data;
    const data2 = response2.data;

    // Render content
    return res.render("platform/plans/update", {
        plan: data2.plan,
        roles: data.roles
    });
});

/*************** Update Plan - PUT ***************/
router.put("/update/:plan_id", require_auth, platform_mod, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const plan_id = req.params.plan_id;

    let highlight_v = "0";
    let highlight_title_v = "none";
    let highlight_subtitle_v = "none";

    let errors = [];
    const notifications = [];

    // Check permissions
    if (!permissions.includes("platform.plans.update")) return res.redirect("/system-alert/403");

    // Body
    const { name, price, description, highlight, highlight_title, highlight_subtitle, cycle, position, role_id } = req.body;

    // Check
    if (highlight == "on") highlight_v = "1";
    if (highlight_title) highlight_title_v = highlight_title;
    if (highlight_subtitle) highlight_subtitle_v = highlight_subtitle;

    // Send Update
    const response = await send_data("/platform/plans/update", {}, {
        name, price, description, cycle, position, role_id, plan_id,

        highlight: highlight_v,
        highlight_title: highlight_title_v,
        highlight_subtitle: highlight_subtitle_v
    }, req);

    // Get Roles & Plan
    const response2 = await get_data("/platform/plans/get_roles", {}, req);
    const response3 = await get_data(`/platform/plans/get/${plan_id}`, {}, req);

    const data2 = response2.data;
    const data3 = response3.data;

    if (response2.error || response3.error) return res.redirect("/platform/plans");

    // Error
    if (response.error) {
        // Error Message
        if (response.details.length > 0) errors = response.details;
        else errors = [response.message];

        return res.render("platform/plans/update", {
            errors,

            plan: data3.plan,
            roles: data2.roles
        })
    }

    notifications.push({
        message: response.message,
        type: "success"
    })

    // Render content
    return res.render("platform/plans/update", {
        notifications,

        plan: data3.plan,
        roles: data2.roles
    });
});


/*************** Export ***************/
export default router
