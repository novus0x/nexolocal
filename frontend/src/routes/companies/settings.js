/*************** Modules ***************/
import fs from 'fs';
import express from 'express';

import upload from '../../middlewares/upload.js';

import { is_valid_certificate_file } from '../../utils/files.js';
import { get_data, send_data, send_form_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Settings Route - GET ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    // Check permissions
    if (!permissions.includes("company.settings.read")) return res.redirect("/system-alert/403");

    // Request Data
    const response = await get_data("/company/settings", {}, req);

    if (response.error) return res.redirect("/platform");

    const data = response.data.information;

    // Render content
    return res.render("companies/settings/main", {
        company: data.company,
        plan: data.plan,
        tax_profile: data.tax_profile,
        tax_subscription: data.tax_subscription
    });
});

/*************** Settings Route - POST ***************/
router.post("/", require_auth, at_least_company, upload.single("file"), async (req, res) => {
    // Variables
    const file = req.file;
    const permissions = req.permissions;

    let errors = [];
    const notifications = [];

    let description_v = "none";
    let phone_v = "none";
    let is_formal_v = "0";

    let legal_name_v = "none";
    let tax_id_v = "none";
    let address_line_v = "none";
    let region_v = "none";
    let city_v = "none";
    let postal_code_v = "none";
    let tax_user_v = "none";
    let tax_password_v = "none";
    let invoice_series_v = "none";
    let invoice_number_v = "none";
    let receipt_series_v = "none";
    let receipt_number_v = "none";
    let certificate_password_v = "none";

    let emission_status_v = "auto";
    let tax_enabled_v = "0";

    // Check permissions
    if (!permissions.includes("company.settings.update")) return res.redirect("/system-alert/403");

    // Get Body
    const { 
        commercial_name, description, email, phone, is_formal, legal_name, tax_id, address_line, region, 
        city, postal_code, tax_user, tax_password, invoice_series, invoice_number, receipt_series, 
        receipt_number, certificate_password, emission_status, tax_enabled
    } = req.body;

    if (description) description_v = description;
    if (phone) phone_v = phone;
    
    if (emission_status) emission_status_v = emission_status;

    if (tax_enabled == "on") tax_enabled_v = "1";
    else tax_enabled_v = "0";

    // Send Data
    const form = new FormData();

    // Only if is formal
    if (is_formal == "on") {
        is_formal_v = "1";

        if (!file) errors.push("No subio ningun archivo");
        
        if (!is_valid_certificate_file(file)) errors.push("Archivo de certificado inválido");

        if (errors.length > 0) {
            const response2 = await get_data("/company/settings", {}, req);

            if (response2.error) return res.redirect("/platform");

            const data2 = response2.data.information;
            const tax_subscription2 = data2.tax_subscription || {};

            return res.render("companies/settings/main", {
                errors,

                commercial_name, description, email, phone, is_formal, legal_name, tax_id, address_line, 
                region, city, postal_code, tax_user, invoice_series, invoice_number, receipt_series, 
                receipt_number, emission_status, tax_enabled,

                company: data2.company,
                plan: data2.plan,
                tax_profile: data2.tax_profile,
                tax_subscription: tax_subscription2
            });
        }

        // File data
        const blob = new Blob([file.buffer], {
            type: file.mimetype
        });

        // Temp Logo
        const buffer = fs.readFileSync("src/public/img/utils/logo-here.png");
        const blob2 = new Blob([buffer], {type: "image/png"});

        // Check Data
        if (legal_name) legal_name_v = legal_name;
        if (tax_id) tax_id_v = tax_id;
        if (address_line) address_line_v = address_line;
        if (region) region_v = region;
        if (city) city_v = city;
        if (postal_code) postal_code_v = postal_code;
        if (tax_user) tax_user_v = tax_user;
        if (tax_password) tax_password_v = tax_password;
        if (invoice_series) invoice_series_v = invoice_series;
        if (invoice_number) invoice_number_v = invoice_number;
        if (receipt_series) receipt_series_v = receipt_series;
        if (receipt_number) receipt_number_v = receipt_number;
        if (certificate_password) certificate_password_v = certificate_password;

        form.append("file", blob, req.file.originalname);
        form.append("logo", blob2, "logo-here.png");
    }

    // Add Data to Form
    form.append("commercial_name", commercial_name);
    form.append("email", email);
    form.append("description", description_v);
    form.append("phone", phone_v);
    form.append("is_formal", is_formal_v);
    
    form.append("legal_name", legal_name_v);
    form.append("tax_id", tax_id_v);
    form.append("address_line", address_line_v);
    form.append("region", region_v);
    form.append("city", city_v);
    form.append("postal_code", postal_code_v);
    form.append("tax_user", tax_user_v);
    form.append("tax_password", tax_password_v);
    form.append("invoice_series", invoice_series_v);
    form.append("invoice_number", invoice_number_v);
    form.append("receipt_series", receipt_series_v);
    form.append("receipt_number", receipt_number_v);
    form.append("certificate_password", certificate_password_v);

    form.append("emission_status", emission_status_v);
    form.append("tax_enabled", tax_enabled_v);

    const response = await send_form_data("/company/settings/update", {}, form, req);

    if (response.error) {
        if (response.details.length > 0) errors = response.details;
        else errors = [response.message];

        const response2 = await get_data("/company/settings", {}, req);

        if (response2.error) return res.redirect("/platform");

        const data2 = response2.data.information;
        const tax_subscription2 = data2.tax_subscription || {};

        return res.render("companies/settings/main", {
            errors,

            commercial_name, description, email, phone, is_formal, legal_name, tax_id, address_line, 
            region, city, postal_code, tax_user, invoice_series, invoice_number, receipt_series, 
            receipt_number,

            company: data2.company,
            plan: data2.plan,
            tax_profile: data2.tax_profile,
            tax_subscription: tax_subscription2
        });
    }

    const response3 = await get_data("/company/settings", {}, req);
    const data3 = response3.data.information;
    const tax_subscription3 = data3.tax_subscription || {};

    notifications.push({
        message: "Negocio Actualizado",
        type: "success"
    })

    // Render content
    return res.render("companies/settings/main", {
        notifications,

        company: data3.company,
        plan: data3.plan,
        tax_profile: data3.tax_profile,
        tax_subscription: tax_subscription3
    });
});

/*************** Export ***************/
export default router
