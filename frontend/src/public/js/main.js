function toggle_company_dropdown(event) {
    if (event) event.stopPropagation();
    const company_dropdown = document.getElementById('company-dropdown');
    const user_dropdown = document.getElementById('user-dropdown');
    if (user_dropdown) user_dropdown.classList.remove('active');
    if (company_dropdown) company_dropdown.classList.toggle('active');
}

function select_company(id, full_name) {
    const current_name = document.getElementById('current-company-name');
    const current_icon = document.getElementById('current-company-icon');

    const company_dropdown = document.getElementById('company-dropdown');
    if (company_dropdown) company_dropdown.classList.remove('active');
}

// User Dropdown
function toggle_user_dropdown(event) {
    if (event) event.stopPropagation();
    const user_dropdown = document.getElementById('user-dropdown');
    const company_dropdown = document.getElementById('company-dropdown');
    if (company_dropdown) company_dropdown.classList.remove('active');
    if (user_dropdown) user_dropdown.classList.toggle('active');
}

function toggle_sidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const sidebar_texts = document.querySelectorAll('.sidebar-text');

    if (window.innerWidth < 1024) {
        const isOpen = !sidebar.classList.contains('-translate-x-full');
        if (isOpen) {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        } else {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
        }
    } else {
        const is_collapsed = sidebar.classList.contains('w-20');
        if (is_collapsed) {
            sidebar.classList.remove('w-20');
            sidebar.classList.add('w-72');
            sidebar_texts.forEach(text => text.classList.remove('hidden'));
        } else {
            sidebar.classList.remove('w-72');
            sidebar.classList.add('w-20');
            sidebar_texts.forEach(text => text.classList.add('hidden'));
        }
    }
}

window.addEventListener('click', () => {
    const company_dropdown = document.getElementById('company-dropdown');
    const user_dropdown = document.getElementById('user-dropdown');
    if (company_dropdown) company_dropdown.classList.remove('active');
    if (user_dropdown) user_dropdown.classList.remove('active');
});

// Inicializar con la primera empresa de forma segura
document.addEventListener('DOMContentLoaded', () => {
    select_company('uid', 'NexoLocal');
});

// Inicializar con el rol seguro
let current_filter_roles = 'platform';

function toggle_filter_roles() {
    const container = document.getElementById('type-switch');
    const opt_system = document.getElementById('opt-system');
    const opt_user = document.getElementById('opt-user');

    // Alternar estado
    container.classList.toggle('checked');
    current_filter_roles = container.classList.contains('checked') ? 'company' : 'platform';

    // Actualizar clases visuales de texto
    if (current_filter_roles === 'company') {
        opt_system.classList.remove('active');
        opt_user.classList.add('active');
        console.log(current_filter_roles);
    } else {
        opt_system.classList.add('active');
        opt_user.classList.remove('active');
        console.log(current_filter_roles);
    }
}
