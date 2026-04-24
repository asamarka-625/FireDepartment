let accessToken = null;
let csrfToken = null;
let refreshTimeout = null;

async function silentRefresh() {
    try {
        const response = await fetch('/api/v1/auth/refresh', { method: 'POST' });

        if (response.ok) {
            const data = await response.json();
            accessToken = data.access_token;
            csrfToken = data.csrf_token;

            if (refreshTimeout) clearTimeout(refreshTimeout);
            refreshTimeout = setTimeout(silentRefresh, 14 * 60 * 1000);

        } else if (window.location.pathname !== '/login') {
            window.location.href = '/login';
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

    let response = await fetch(url, { ...options, headers });

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

            window.location.href = data.redirect || "/login";
        }
    } catch (error) {
        console.error("Ошибка выхода из сессии", error);
    }
}


document.querySelectorAll(".accordion").forEach(btn => {
    btn.addEventListener("click", function () {
        const panel = this.nextElementSibling;

        panel.style.display =
            panel.style.display === "block" ? "none" : "block";
    });
});