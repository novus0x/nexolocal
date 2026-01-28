/*************** Modules ***************/
import express from 'express';

import { get_data, send_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Finance route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let items = [];
    let finance = {};

    // Check permissions
    if (!permissions.includes("company.incomes.read") || !permissions.includes("company.expenses.read")) return res.redirect("/");

    // Request
    const response = await get_data("/company/finance", {}, req);

    if (response.error) {
        return res.redirect("/")
    }
    const data = response.data;

    items = data.items;
    finance = data.finance;

    // Render content
    return res.render("companies/finance/main", {
        finance,
        finance_items: items
    });
});

/*************** New Entrance - GET ***************/
router.get("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.incomes.create") || !permissions.includes("company.expenses.create")) return res.redirect("/");

    // Render content
    return res.render("companies/finance/create", {});
});

/*************** New Entrance - POST ***************/
router.post("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    let description_v = "No Description";
    let subcategory_v = "No Category";
    let expense_category_v = "No Category";
    let receipt_url_v = "No URL";

    // Check permissions
    if (!permissions.includes("company.incomes.create") || !permissions.includes("company.expenses.create")) return res.redirect("/");

    const { amount, title, description, expense_category, subcategory, date, receipt_url } = req.body;

    if (description) description_v = description;
    if (expense_category) expense_category_v = expense_category;
    if (subcategory) subcategory_v = subcategory;

    const response = await send_data("/company/finance/create", {}, {
        description: description_v,
        receipt_url: receipt_url_v,
        subcategory: subcategory_v, 
        expense_category: expense_category_v,
        amount, title, date
    }, req)

    if (response.error) {
        return res.render("companies/finance/create", {
            errors: response.details,
            amount, title, description, expense_category, subcategory, date, receipt_url
        })
    }

    // Render content
    return res.redirect(`/companies/${company_id}/finance`);
});

/*************** Export ***************/
export default router
