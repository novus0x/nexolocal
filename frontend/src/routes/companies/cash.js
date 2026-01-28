/*************** Modules ***************/
import express from 'express';

import { require_auth, at_least_company } from '../../middlewares/auth.js';
import { get_data, send_data } from '../../utils/api.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Main route ***************/
router.post("/open", require_auth, at_least_company, async (req, res) => {
    // Variables
    const user = req.user;
    const permissions = req.permissions;

    const company_id = req.params.company_id;

    // Check permissions
    if (!permissions.includes("company.cash.open")) return res.redirect("/");

    const { initial_cash } = req.body;
    console.log(initial_cash)

    const response = await send_data("/company/cash/open", {}, {
        initial_cash
    }, req)

    if (response.error) {
        if (!permissions.includes("company.read")) return res.redirect("/");

        const response2 = await get_data("/company/dashboard", {}, req);

        if (response2.error) return res.redirect("/");

        const data = response2.data;

        // Render content
        return res.render("companies/dashboard", {
            company: data.company,
            products: data.products
        });
    }

    // Render content
    return res.redirect(`/companies/${company_id}`)
});

/*************** Export ***************/
export default router
