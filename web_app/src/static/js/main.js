let accessToken = null;
let csrfToken = null;
let refreshTimeout = null;

async function silentRefresh() {
    try {
        const response = await fetch('/72tldh/api/v1/auth/refresh', { method: 'POST' });

        if (response.ok) {
            const data = await response.json();
            accessToken = data.access_token;
            csrfToken = data.csrf_token;

            if (refreshTimeout) clearTimeout(refreshTimeout);
            refreshTimeout = setTimeout(silentRefresh, 14 * 60 * 1000);

        } else if (window.location.pathname !== '/72tldh/login') {
            window.location.href = '/72tldh/login';
        }
    } catch (error) {
        console.error("Ошибка фонового обновления");
    }
}

async function apiRequest(url, options = {}) {
    if (!accessToken) await silentRefresh();

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'X-CSRF-Token': csrfToken,
        ...options.headers
    };

    let response = await fetch(`/72tldh${url}`, { ...options, headers });

    if (response.status === 401) {
        await silentRefresh();
        headers['Authorization'] = `Bearer ${accessToken}`;
        headers['X-CSRF-Token'] = csrfToken;
        response = await fetch(url, { ...options, headers });
    }

    return response;
}

async function logoutRequest() {
    try {
        const response = await apiRequest('/api/v1/auth/logout', {
            method: 'POST'
        });

        if (response.ok) {
            const data = await response.json();
            accessToken = null;
            csrfToken = null;
            if (refreshTimeout) clearTimeout(refreshTimeout);

            window.location.href = data.redirect || "/72tldh/login";
        }
    } catch (error) {
        console.error("Ошибка выхода из сессии", error);
    }
}

function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s forwards";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.getElementById("logoutBtn");

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            await logoutRequest();
        });
    }

    document.querySelectorAll(".accordion").forEach(btn => {
        btn.addEventListener("click", function () {
            const panel = this.nextElementSibling;

            panel.style.display =
                panel.style.display === "block" ? "none" : "block";
        });
    });
});