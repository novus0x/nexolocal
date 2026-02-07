/*************** Modules ***************/
import express from 'express';
import cookie_parser from 'cookie-parser';
import method_override from 'method-override';

import nunjucks from 'nunjucks';

import auth from './routes/auth/auth.js';
import oauth from './routes/auth/oauth.js';

import users_settings from './routes/users/settings.js';

import general_main from './routes/general/main.js';
import general_invitations from './routes/general/invitations.js';
import general_check_ticket from './routes/general/check_ticket.js';

import platform_main from './routes/platform/main.js';
import platform_users from './routes/platform/users.js';
import platform_roles from './routes/platform/roles.js';
import platform_companies from './routes/platform/companies.js';
import platform_analytics from './routes/platform/analytics.js';

import companies_main from './routes/companies/main.js';
import companies_cash from './routes/companies/cash.js';
import companies_finance from './routes/companies/finance.js';
import companies_products from './routes/companies/products.js';
import companies_sales from './routes/companies/sales.js'
import companies_settings from './routes/companies/settings.js';

import users_api from './routes/users/api.js';
import companies_api from './routes/companies/api.js';

import system_alerts_main from './routes/system_alerts/main.js';

import settings from './settings.js';

/*************** Variables ***************/
const app = express();
const PORT = settings.port;

/*************** Settings ***************/
app.use("/public", express.static("src/public"));
app.use(cookie_parser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(method_override((req) => {
    if (req.body && typeof req.body === "object" && "_method" in req.body) {
        const method = req.body._method.toUpperCase();
        delete req.body._method;
        return method;
    }
}));

nunjucks.configure("src/views", {
    autoescape: true,
    express: app,
    noCache: true
});

app.locals.update_query = (query, updates) => {
    const params = new URLSearchParams(query);

    for (const [key, value] of Object.entries(updates)) {
        if (value === null || value === undefined) {
            params.delete(key);
        } else {
            params.set(key, value);
        }
    }

    const qs = params.toString();
    
    return qs ? `?${qs}` : "";
};

app.set("view engine", "njk");

/*************** Routes ***************/
app.use((req, res, next) => {
    console.log("METHOD:", req.method, "URL:", req.url);
    next();
});

app.use("/", general_main);
app.use("/", general_check_ticket);
app.use("/invitations", general_invitations);

app.use("/auth", auth);
app.use("/oauth", oauth);

app.use("/users", users_settings);

app.use("/platform", platform_main);
app.use("/platform/companies", platform_companies);
app.use("/platform/users", platform_users);
app.use("/platform/roles", platform_roles);
app.use("/platform/analytics", platform_analytics);

app.use("/companies", companies_main);
app.use("/companies/:company_id/cash", companies_cash);
app.use("/companies/:company_id/products", companies_products);
app.use("/companies/:company_id/finance", companies_finance);
app.use("/companies/:company_id/sales", companies_sales);
app.use("/companies/:company_id/settings", companies_settings);

app.use("/users/api", users_api);
app.use("/companies/:company_id/api", companies_api);

app.use("/system-alert/", system_alerts_main);

app.use((req, res) => {
    return res.redirect("/system-alert/404")
});

/*************** Run App ***************/
app.listen(PORT, () => {
    console.log(`App running on port ${PORT}`);
});
