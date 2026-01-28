/*************** Modules ***************/
import settings from "../settings.js";

/********************** GET Request **********************/
export async function get_data(endpoint, headers, req) {
    // Variables
    let i, details, values = {
        error: false,
        message: "",
        details: [],
        data: {}
    };

    const final_headers = {
        "Content-Type": "application/json",
        ...headers
    };

    if (req?.headers?.cookie) {
        final_headers.Cookie = req.headers.cookie;
    }

    if (req?.headers?.["accept-language"]) {
        final_headers["Accept-Language"] = req.headers["accept-language"];
    }

    // Request
    const res = await fetch(`${settings.api_url}${endpoint}`, {
        method: 'GET',
        headers: final_headers
    })

    // Get data
    const data = await res.json();

    // Set Message
    values.message = data.message;

    // Check errors
    if (data.status == 400) {
        values.error = true;
        details = data.details;

        // Multiple errors
        if (details) {
            for (i = 0; i < details.length; i++) {
                values.details.push(`${details[i].message}`);
            }
        }

        // Errors
        return values;
    }

    values.data = {
        ...values.data,
        ...(data?.data ?? {})
    };

    // Success
    return values;
}

/********************** POST Request **********************/
export async function send_data(endpoint, headers, body, req) {
    // Variables
    let i, details, values = {
        error: false,
        message: "",
        details: [],
        data: {}
    };

    const final_headers = {
        "Content-Type": "application/json",
        ...headers
    };

    if (req?.headers?.cookie) {
        final_headers.Cookie = req.headers.cookie;
    }

    if (req?.headers?.["accept-language"]) {
        final_headers["Accept-Language"] = req.headers["accept-language"];
    }

    // Request
    const res = await fetch(`${settings.api_url}${endpoint}`, {
        method: 'POST',
        headers: final_headers,
        body: JSON.stringify(body),
    })

    // Get data
    const data = await res.json();
    const cookie_value = res.headers.get("set-cookie");

    // Set Message
    values.message = data.message;

    // Check errors
    if (data.status == 400) {
        values.error = true;
        details = data.details;

        // Multiple errors
        if (details) {
            for (i = 0; i < details.length; i++) {
                values.details.push(`${details[i].message}`);
            }
        }

        // Errors
        return values;
    }

    // All Good
    if (cookie_value) {
        values.data["cookie_value"] = cookie_value;
    } else {
        values.data["cookie_value"] = false;
    }

    values.data = {
        ...values.data,
        ...(data?.data ?? {})
    };

    // Success
    return values;
};

/********************** POST Form Data **********************/
export async function send_form_data(endpoint, headers = {}, form, req) {
    let values = {
        error: false,
        message: "",
        details: [],
        data: {}
    };

    const final_headers = {
        ...headers
    };

    if (req?.headers?.cookie) {
        final_headers.Cookie = req.headers.cookie;
    }

    if (req?.headers?.["accept-language"]) {
        final_headers["Accept-Language"] = req.headers["accept-language"];
    }

    const res = await fetch(`${settings.api_url}${endpoint}`, {
        method: "POST",
        headers: final_headers,
        body: form
    });

    const data = await res.json();
    const cookie_value = res.headers.get("set-cookie");

    values.message = data.message ?? "";

    if (!res.ok || data.status === 400) {
        values.error = true;

        if (data.details) {
            for (const d of data.details) {
                values.details.push(d.message);
            }
        }

        return values;
    }

    if (cookie_value) {
        values.data.cookie_value = cookie_value;
    }

    values.data = {
        ...values.data,
        ...(data?.data ?? {})
    };

    return values;
}
