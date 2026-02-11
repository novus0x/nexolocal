/*************** Modules ***************/
import setting from '../settings.js';

import { get_data, send_data } from '../utils/api.js';
import { get_scopes } from '../utils/permissions.js';

/*************** Variables ***************/
const token_name = setting.token_name;

/*************** Auth Protection ***************/
export async function require_auth(req, res, next) {
    // Variables
    const token = req.cookies?.[token_name];
    let permissions = [];
    let company_value = {};

    if (!token) {
        return res.redirect("/auth");
    }

    const response = await get_data("/auth/user", {}, req);

    if (!response.data.user) {
        res.clearCookie(token_name);
        return res.redirect("/auth/logout");
    }

    if (response.data.permissions.length > 0) permissions = response.data.permissions;

    // Check if id exist (/companies/:id)
    const company_id = req.params.company_id;
    let check_comp = true;

    if (company_id) {
        if (req.cookies.company_id) {
            const cookie_val = req.cookies.company_id;

            if (cookie_val.id == company_id) {
                check_comp = false
                company_value = cookie_val;
            };
        }

        if (check_comp) {
            const response_permissions = await send_data("/company/companies/validate_company_id", {}, { company_id }, req);

            if (response_permissions.error) {
                res.clearCookie("company_id");
                return res.redirect("/");
            }

            const company = response_permissions.data.company;

            res.cookie("company_id", company, {
                httpOnly: false,
                sameSite: "lax",
                secure: false,
                path: "/"
            });

            return res.redirect(req.originalUrl);
        }
    }

    const user = response.data.user;
    const invitations = response.data.invitations;

    if (user.is_blocked) return res.redirect("/system-alert/403");

    req.user = user;
    req.permissions = permissions;
    req.company_id = company_value.id;

    res.locals.user = user;
    res.locals.permissions = permissions;
    res.locals.scopes = get_scopes(permissions);
    res.locals.user_companies = user.user_companies;
    res.locals.invitations_sidebar = invitations;
    res.locals.company_information = company_value;

    return next();
}

/*************** Specific Permissions ***************/
export async function platform_mod(req, res, next) {
    // Variables
    const permissions = req.permissions;
    const scopes = get_scopes(permissions);

    // If platform mod
    if (scopes.platform) return next();

    return res.redirect("/companies");
}

/*************** No Company ***************/
export async function no_permissions(req, res, next) {
    // Variables
    const permissions = req.permissions;
    const scopes = get_scopes(permissions);

    if (scopes.platform) return res.redirect("/platform");
    else if (scopes.company) return res.redirect("/companies")

    return next();
}

/*************** Require at least Company ***************/
export async function at_least_company(req, res, next) {
    // Variables
    const permissions = req.permissions;
    const scopes = get_scopes(permissions);

    if (scopes.platform) return next();
    else if (scopes.company) return next();

    return res.redirect("/dashboard");
}

/*************** Already Login ***************/
export async function already_login(req, res, next) {
    const token = req.cookies?.[token_name];

    if (token) {
        return res.redirect("/platform")
    }

    return next();
}
