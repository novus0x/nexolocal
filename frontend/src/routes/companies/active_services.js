/*************** Modules ***************/
import express from 'express';

import { create_params } from '../../utils/params.js';
import { get_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Active Services Route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    /*************** Variables ***************/
    const permissions = req.permissions;
    const page = parseInt(req.query.page || "1", 10);
    const current_page = Math.max(page, 1);
    const status = req.query.status;
    const type_of = req.query.type;
    const q = req.query.q;

    /*************** Check permissions ***************/
    if (!permissions.includes("company.active_services.read")) return res.redirect("/system-alert/403");

    /*************** Request ***************/
    const params = create_params({
        page: current_page,
        status: status,
        type_of: type_of,
        q: q
    });

    const response = await get_data(`/company/active_services${params}`, {}, req);

    if (response.error) {
        return res.redirect("/");
    }

    const data = response.data;

    /*************** Render content ***************/
    return res.render("companies/active-services/main", {
        items_quantity: data.items_quantity || 0,
        active_quantity: data.active_quantity || 0,
        expired_quantity: data.expired_quantity || 0,
        services: data.services || [],
        pagination: data.pagination || { next: false, back: false, q_pages: 1 },
        page: current_page,

        query: req.query
    });
});

/*************** Export ***************/
export default router
