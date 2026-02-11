/*************** Modules ***************/
import express, { response } from 'express';

import upload from '../../middlewares/upload.js';

import { is_csv } from '../../utils/files.js'
import { create_params } from '../../utils/params.js';
import { svg_generator } from '../../utils/generator.js';
import { get_data, send_data, send_form_data } from '../../utils/api.js';
import { require_auth, at_least_company } from '../../middlewares/auth.js';

/*************** Variables ***************/
const router = express.Router({ mergeParams: true });

/*************** Main route ***************/
router.get("/", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const page = parseInt(req.query.page || "1", 10);
    const current_page = Math.max(page, 1);

    const type_of = req.query.type;
    const q = req.query.q;

    // Check permissions
    if (!permissions.includes("company.products.read")) return res.redirect("/system-alert/403");

    // Request
    const params = create_params({ page: current_page, type_of: type_of, q: q });
    const response = await get_data(`/company/products${params}`, {}, req);

    const data = response.data;

    // Render content
    return res.render("companies/products/main", {
        items_quantity: data.items_quantity,
        products: data.products,
        low_products_quantity: data.low_products_quantity,
        stock_value: data.stock_value,
        pagination: data.pagination,
        page: current_page,

        query: req.query
    });
});

/*************** Create Product - GET ***************/
router.get("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    let suppliers = [];

    // Check permissions
    if (!permissions.includes("company.products.create")) return res.redirect("/system-alert/403");

    // Get data
    const response = await get_data("/company/products/create", {}, req);

    if (response.error) suppliers = [];

    const data = response.data;

    suppliers = data.suppliers;

    // Render content
    return res.render("companies/products/create", {
        suppliers
    });
});

/*************** Create Product - POST ***************/
router.post("/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;
    const company_id = req.company_id;

    let tax_include_v = "0";
    let is_bulk_v = "0";
    let is_service_v = "0";
    let duration_v = "0";
    let stock_v = "0";
    let track_product_v = "0";
    let low_stock_v = "0";
    let bonus_v = "0";
    let description_v = "No description";
    let supplier_id_v = "none";
    let date_val = new Date().toISOString().split("T")[0];

    let weight_v = "0";
    let height_v = "0";
    let width_v = "0";
    let length_v = "0";

    let errors = [];
    let suppliers = [];

    // Check permissions
    if (!permissions.includes("company.products.create")) return res.redirect("/system-alert/403");

    // Get POST data
    const { name, sku, identifier, category, description, supplier_id, sale_price, sale_cost, tax_include, is_bulk, is_service, duration, duration_type, staff_id, stock, track_product, low_stock, bonus, expiration_date, weight, length, width, height } = req.body;

    if (stock) stock_v = stock;
    if (description) description_v = description;
    if (supplier_id) supplier_id_v = supplier_id;

    if (is_bulk == "on") is_bulk_v = "1";

    if (is_service == "on") {
        is_service_v = "1"
        duration_v = duration;
    }

    if (track_product == "on") {
        track_product_v = "1";
        if (!low_stock) low_stock_v = 5;
        else low_stock_v = low_stock;
    }

    if (tax_include == "on") tax_include_v = "1";

    if (expiration_date) date_val = expiration_date;

    if (weight) weight_v = weight;
    if (length) length_v = length;
    if (width) width_v = width;
    if (height) height_v = height;
    if (bonus) bonus_v = bonus;

    const response = await send_data("/company/products/create", {}, {
        name, sku, identifier, category, sale_price, sale_cost, staff_id,
        duration_type,

        weight: weight_v,
        length: length_v,
        width: width_v,
        height: height_v,

        bonus: bonus_v,
        stock: stock_v,
        description: description_v,
        supplier_id: supplier_id_v,
        tax_include: tax_include_v,
        is_bulk: is_bulk_v,
        is_service: is_service_v,
        duration: duration_v,
        track_product: track_product_v,
        low_stock: low_stock_v,
        expiration_date: date_val
    }, req);

    if (response.error) {
        if (response.details.length <= 0) errors = response.message;
        else errors = [response.details];

        const response2 = await get_data("/company/products/create", {}, req);

        if (response2.error) suppliers = [];

        const data2 = response2.data;

        suppliers = data2.suppliers;

        return res.render("companies/products/create", {
            errors: response.details,

            suppliers,
            name, sku, identifier, supplier_id, category, description, sale_price, sale_cost,
            tax_include, is_service, duration, duration_type, staff_id, stock, track_product,
            low_stock, bonus, weight, length, width, height, date_val
        })
    }

    const data = response.data;

    return res.redirect(`/companies/${company_id}/products/read/${data.product_id}`);
});

/*************** Import Products - CSV - GET ***************/
router.get("/import", require_auth, at_least_company, async (req, res) => {
    // Variables
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.products.import.csv")) return res.redirect("/system-alert/403");

    // Render content
    return res.render("companies/products/import", {});
});

/*************** Import Products - CSV - POST ***************/
router.post("/import", require_auth, at_least_company, upload.single("file"), async (req, res) => {
    // Variables
    const file = req.file;
    const company_id = req.company_id;
    const permissions = req.permissions;

    // Check permissions
    if (!permissions.includes("company.products.import.csv")) return res.redirect("/system-alert/403");

    // Validations
    if (!file) {
        return res.render("companies/products/import", {
            errors: ["No subio ningun archivo"]
        });
    }

    if (!is_csv(file)) {
        return res.render("companies/products/import", {
            errors: ["Archivo Invalido"]
        });
    }

    // Create Form Data
    const form = new FormData();
    const blob = new Blob([req.file.buffer], {
        type: req.file.mimetype
    })

    form.append("company_id", company_id);
    form.append("file", blob, req.file.originalname);

    // Send Data
    const response = await send_form_data("/company/products/import", {}, form, req);

    if (response.error) {
        return res.render("companies/products/import", {
            errors: [response.message]
        })
    }

    // Redirect
    return res.redirect(`/companies/${company_id}/products`);
});

/*************** View Product ***************/
router.get("/read/:product_id", require_auth, at_least_company, async (req, res) => {
    // Variables
    const company_id = req.company_id;
    const permissions = req.permissions;
    const product_id = req.params.product_id;

    let product_v = {};
    let dimensions_v = [];
    let batchs_v = [];
    let batchs_len_v = 0;
    let supplier = {};

    // Check permissions
    if (!permissions.includes("company.products.read")) return res.redirect("/system-alert/403");

    // Request
    const response = await get_data(`/company/products/get/${product_id}`, {}, req);

    if (response.error) return res.redirect(`/company/${company_id}/products`);

    const data = response.data;

    product_v = data.product;
    batchs_v = data.batchs;
    batchs_len_v = batchs_v.length;
    supplier = data.supplier;

    const qrcode_v = await svg_generator(product_v.identifier, "qrcode");
    const barcode_v = await svg_generator(product_v.identifier, "barcode");

    dimensions_v = product_v.dimensions.split("x");

    if (dimensions_v.length < 3) {
        dimensions_v = [0, 0, 0]
    }

    // Render content
    return res.render("companies/products/read", {
        supplier,

        qrcode: qrcode_v,
        barcode: barcode_v,
        product: product_v,
        dimensions: dimensions_v,
        batchs: batchs_v,
        batchs_len: batchs_len_v
    });
});

/*************** View Product Baths ***************/
router.get("/:product_id/batchs", require_auth, at_least_company, async (req, res) => {
    // Variables
    const company_id = req.company_id;
    const permissions = req.permissions;
    const product_id = req.params.product_id;

    // Check permissions
    if (!permissions.includes("company.products.read")) return res.redirect("/system-alert/403");

    return res.json("batchs");
});

/*************** Create Product Batch - GET ***************/
router.get("/:product_id/batchs/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const company_id = req.company_id;
    const permissions = req.permissions;
    const product_id = req.params.product_id;

    // Check permissions
    if (!permissions.includes("company.products.create")) return res.redirect("/system-alert/403");

    // Request
    const response = await get_data(`/company/products/${product_id}/batchs/create`, {}, req);

    if (response.error) return res.redirect(`/company/${company_id}/products`);

    const data = response.data;

    const product = data.product || {};
    const today_inp = new Date().toISOString().split("T")[0];

    // Render content
    return res.render("companies/products/batchs/create", {
        today_inp,
        product: product
    });
});

/*************** Create Product Batch - POST ***************/
router.post("/:product_id/batchs/create", require_auth, at_least_company, async (req, res) => {
    // Variables
    const company_id = req.company_id;
    const permissions = req.permissions;
    const product_id = req.params.product_id;

    let expiration_date_v = new Date().toISOString().split("T")[0];
    let reception_date_v = new Date().toISOString().split("T")[0];

    // Check permissions
    if (!permissions.includes("company.products.create")) return res.redirect("/system-alert/403");

    const { quantity, bonus, price, cost, reception_date, expiration_date } = req.body;

    if (expiration_date) expiration_date_v = expiration_date;
    if (reception_date) reception_date_v = reception_date;

    // Request
    const response = await send_data(`/company/products/${product_id}/batchs/create`, {}, {
        product_id, quantity, bonus, price, cost,

        reception_date: reception_date_v,
        expiration_date: expiration_date_v
    }, req);

    if (response.error) {
        let errors = []

        if (response.details.length <= 0) errors.push(response.message);
        else errors = response.details;

        const response2 = await get_data(`/company/products/${product_id}/batchs/create`, {}, req);

        const data = response2.data;
        const product = data.product || {};

        return res.render("companies/products/batchs/create", {
            errors: errors,
            quantity, price, cost,

            today_inp: reception_date_v,
            expiration_date: expiration_date_v,
            product: product
        });
    }

    // Render content
    return res.redirect(`/companies/${company_id}/products/read/${product_id}`);
});

/*************** Export ***************/
export default router
