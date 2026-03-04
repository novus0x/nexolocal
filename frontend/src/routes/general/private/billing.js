/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../../utils/api.js';
import { require_auth } from '../../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router();

/*************** Billing ***************/
router.get("/", require_auth, async (req, res) => {
    // Variables
    let billing_overview = {
        items: [],
        next_item: {
            available: false
        },
        pending_count: 0
    };

    // Get Overview
    const response = await get_data("/general/billing/overview", {}, req);

    if (response.error == false) {
        billing_overview = response.data.billing_overview;
    }

    return res.render("general/private/billing/main", {
        billing_overview
    });
});

/*************** Billing - Plans ***************/
router.get("/plans", require_auth, async (req, res) => {
    // Variables
    let plans = [];
    let companies_q = 0;

    // Get Plans
    const response = await get_data("/general/billing/plans", {}, req);

    if (response.error == false) {
        plans = response.data.plans;
        companies_q = response.data.companies_q;
    }

    return res.render("general/private/billing/plans/main", {
        plans, companies_q
    });
});

/*************** Select Plan - GET ***************/
router.get("/plans/:plan_id", require_auth, async (req, res) => {
    // Variables
    const plan_id = req.params.plan_id;

    // Get Plan
    const response = await get_data(`/general/billing/plans/${plan_id}`, {}, req);

    if (response.error) return res.redirect("/dashboard/billing/plans");

    const data = response.data;

    return res.render("general/private/billing/plans/choose", {
        plan: data.plan,
        companies_q: data.companies_q
    });
});

/*************** Select Plan - POST ***************/
router.post("/plans/:plan_id", require_auth, async (req, res) => {
    // Variables
    const plan_id = req.params.plan_id;

    let errors = [];

    // Get Body
    const { name } = req.body;

    // Get Plan
    const response = await send_data(`/general/billing/plans`, {}, {
        name, plan_id
    }, req);

    if (response.error) {
        const response2 = await get_data(`/general/billing/plans/${plan_id}`, {}, req);

        if (response2.error) return res.redirect("/dashboard/billing/plans");

        if (response.details.length > 0) errors = response.details;
        else errors = [response.message];

        const data2 = response2.data;

        return res.render("general/private/billing/plans/choose", {
            errors, name,

            plan: data2.plan,
            companies_q: data2.companies_q
        });
    }

    const data = response.data;
    const trial = data.trial;
    const company_id = data.company_id;

    if (trial) return res.redirect(`/companies/${company_id}`);
    else return res.redirect(`${data.payment_url}`);
});

/*************** Select Plan - POST ***************/
router.post("/plans/:plan_id/validate", async (req, res) => {
    // Variables
    const company_id = req.query.company_id || "no_data";

    // Body
    const { token } = req.body;

    // Request
    const response = await send_data("/general/billing/validate", {}, {
        token, company_id
    }, req);

    if (response.error) return res.redirect("/dashboard")

    return res.redirect(`/companies/${company_id}`);
});

/*************** Renew Company Subscription - Validate ***************/
router.post("/renew/validate", async (req, res) => {
    // Variables
    const company_id = req.query.company_id || "no_data";

    // Body
    const { token } = req.body;

    // Request
    const response = await send_data("/general/billing/validate", {}, {
        token, company_id
    }, req);

    if (response.error) return res.redirect("/dashboard/billing");

    return res.redirect("/dashboard/billing");
});

/*************** Renew Company Subscription ***************/
router.post("/renew/:id", require_auth, async (req, res) => {
    // Variables
    const id = req.params.id;

    // Request
    const response = await send_data("/general/billing/renew", {}, {
        company_id: id
    }, req);

    if (response.error) return res.redirect("/dashboard/billing");

    return res.redirect(`${response.data.payment_url}`);
});

/*************** Billing - History ***************/
router.get("/history", require_auth, async (req, res) => {
    // Variables

    // Get History
    const response = await get_data("/general/billing/history", {}, req);
    
    if (response.error) return res.redirect("/dashboard/billing");

    // Set Data
    const data = response.data;

    // Render
    return res.render("general/private/billing/history/main", {
        history: data.history
    })
})

/*************** Export ***************/
export default router;
