/*************** Sidebar Active ***************/
export function get_sidebar_active(req) {
    // Variables
    const raw_path = req.originalUrl || req.path || "/";
    const [pathname] = raw_path.split("?");
    const path = pathname || "/";
    const segments = path.split("/").filter(Boolean);

    const section = segments[0] || "";
    const sub_section = segments[1] || "";
    const third_segment = segments[2] || "";

    const company_id = segments[1] || "";
    const company_section = segments[2] || "";
    const normalized_company_section = company_section.replaceAll("-", "_");

    let base_path = path;
    let company_path = null;
    let key = null;

    // Keys
    const general_keys = {
        dashboard: {
            "": "general.home",
            support: "general.support"
        },
        invitations: "general.invitations"
    };

    const platform_keys = {
        "": "platform.dashboard",
        roles: "platform.roles",
        plans: "platform.plans",
        companies: "platform.companies",
        users: "platform.users",
        support: "platform.support",
        analytics: "platform.analytics"
    };

    const company_keys = {
        "": "company.home",
        team: "company.team",
        suppliers: "company.suppliers",
        active_services: "company.active_services",
        products: "company.products",
        cash: "company.cash",
        sales: "company.sales",
        finance: "company.finance",
        analytics: "company.analytics",
        taxes: "company.taxes",
        settings: "company.settings"
    };

    // Operations: General
    if (section === "dashboard") {
        base_path = sub_section ? `/dashboard/${sub_section}` : "/dashboard";
        key = general_keys.dashboard[sub_section] || null;

        if (sub_section === "support" && third_segment === "tickets") {
            key = "general.tickets";
        }
    }

    if (section === "invitations") {
        key = general_keys.invitations;
    }

    // Operations: Platform
    if (section === "platform") {
        base_path = sub_section ? `/platform/${sub_section}` : "/platform";
        key = platform_keys[sub_section] || null;
    }

    // Operations: Companies
    if (section === "companies" && company_id) {
        company_path = company_section
            ? `/companies/${company_id}/${company_section}`
            : `/companies/${company_id}`;

        base_path = company_path || "/companies";
        key = company_keys[normalized_company_section] || null;
    }

    // Response
    return {
        key,
        path,
        base_path,
        company_path
    };
}
