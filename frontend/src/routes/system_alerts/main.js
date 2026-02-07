/*************** Modules ***************/
import express from 'express';

/*************** Variables ***************/
const router = express.Router();

/*************** 403 Forbidden ***************/
router.get("/403", async (req, res) => {
    // Render content
    res.clearCookie("company_id"); // In case exists
    return res.status(403).render("system_alerts/403");
});

/*************** 404 - Not Found ***************/
router.get("/404", async (req, res) => {
    // Render content
    return res.status(404).render("system_alerts/404");
});

/*************** Export ***************/
export default router
