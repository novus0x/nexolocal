function set_sidebar_cookie(state) {
    const date = new Date();
    date.setTime(date.getTime() + (7 * 24 * 60 * 60 * 1000)); // 7 días
    document.cookie = "sidebar_closed=" + state + ";expires=" + date.toUTCString() + ";path=/";
}

function get_sidebar_cookie() {
    const name = "sidebar_closed=";
    const ca = document.cookie.split(";");
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}

document.addEventListener("DOMContentLoaded", () => {
    const is_closed = get_sidebar_cookie();
    const sidebar = document.getElementById("sidebar");
    const sidebar_texts = document.querySelectorAll(".sidebar-text");

    if (is_closed === "true" && window.innerWidth >= 1024) {
        sidebar.classList.remove("w-72");
        sidebar.classList.add("w-20");
        sidebar_texts.forEach(text => text.classList.add("hidden"));
    }

    setTimeout(() => {
        if (sidebar) sidebar.classList.add("sidebar-transition")
    }, 50);
});

function toggle_sidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const sidebar_texts = document.querySelectorAll(".sidebar-text");

    if (window.innerWidth < 1024) {
        const is_hidden = sidebar.classList.contains("-translate-x-full");

        if (is_hidden) {
            sidebar.classList.remove("-translate-x-full");
            overlay.classList.remove("hidden");
        } else {
            sidebar.classList.add("-translate-x-full");
            overlay.classList.add("hidden");
        }
    } else {
        const is_collapsed = sidebar.classList.contains("w-20");

        if (is_collapsed) {
            sidebar.classList.remove("w-20");
            sidebar.classList.add("w-72");
            sidebar_texts.forEach(text => text.classList.remove("hidden"));
            set_sidebar_cookie("false");
        } else {
            sidebar.classList.remove("w-72");
            sidebar.classList.add("w-20");
            sidebar_texts.forEach(text => text.classList.add("hidden"));
            set_sidebar_cookie("true");
        }
    }
}

function toggle_company_dropdown(event) {
    if (event) event.stopPropagation();
    const company_dropdown = document.getElementById("company-dropdown");
    const user_dropdown = document.getElementById("user-dropdown");
    if (user_dropdown) user_dropdown.classList.remove("active");
    if (company_dropdown) company_dropdown.classList.toggle("active");
}

function select_company(id, full_name) {
    const current_name = document.getElementById("current-company-name");
    const current_icon = document.getElementById("current-company-icon");

    const company_dropdown = document.getElementById("company-dropdown");
    if (company_dropdown) company_dropdown.classList.remove("active");
}

function toggle_user_dropdown(event) {
    if (event) event.stopPropagation();
    const user_dropdown = document.getElementById("user-dropdown");
    const company_dropdown = document.getElementById("company-dropdown");
    if (company_dropdown) company_dropdown.classList.remove("active");
    if (user_dropdown) user_dropdown.classList.toggle("active");
}

window.addEventListener("click", () => {
    const company_dropdown = document.getElementById("company-dropdown");
    const user_dropdown = document.getElementById("user-dropdown");
    if (company_dropdown) company_dropdown.classList.remove("active");
    if (user_dropdown) user_dropdown.classList.remove("active");
});

// Inicializar con la primera empresa de forma segura
document.addEventListener("DOMContentLoaded", () => {
    select_company("uid", "NexoLocal");
});

// Inicializar con el rol seguro
let current_filter_roles = "platform";

function toggle_filter_roles() {
    const container = document.getElementById("type-switch");
    const opt_system = document.getElementById("opt-system");
    const opt_user = document.getElementById("opt-user");

    // Alternar estado
    container.classList.toggle("checked");
    current_filter_roles = container.classList.contains("checked") ? "company" : "platform";

    // Actualizar clases visuales de texto
    if (current_filter_roles === "company") {
        opt_system.classList.remove("active");
        opt_user.classList.add("active");
    } else {
        opt_system.classList.add("active");
        opt_user.classList.remove("active");
    }
}
