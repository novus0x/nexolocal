function notify(message, type = 'info', timeout = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return; // 👈 clave

    const notif = document.createElement('div');
    notif.className = `notification notif-${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'i'
    };

    notif.innerHTML = `
        <div class="notif-icon">${icons[type] || icons.info}</div>
        <div class="notif-content">
            <p class="text-sm font-medium">${message}</p>
        </div>
        <div class="notif-close">✕</div>
    `;

    // Cierre manual
    notif.querySelector('.notif-close').addEventListener('click', () => {
        closeNotif(notif);
    });

    container.appendChild(notif);

    // Forzar animación
    requestAnimationFrame(() => {
        notif.classList.add('show');
    });

    // Auto-close
    if (timeout > 0) {
        setTimeout(() => closeNotif(notif), timeout);
    }
}

function closeNotif(el) {
    if (!el || el.classList.contains('hide')) return;

    el.classList.add('hide');

    const remove = () => el.remove();
    el.addEventListener('transitionend', remove, { once: true });

    // Fallback
    setTimeout(remove, 600);
}
