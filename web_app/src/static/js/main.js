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

function showMissingSections(sections) {
    const box = document.getElementById("missingSections");
    const list = box.querySelector(".missing-list");

    list.innerHTML = "";

    if (!sections.length) {
        // detail пустой — показываем общий тост
        box.classList.add("hidden");
        showToast("Не все подразделения подали записку", "error");
        return;
    }

    sections.forEach(title => {
        const li = document.createElement("li");
        li.textContent = title;   // textContent, не innerHTML — без XSS
        list.appendChild(li);
    });

    box.classList.remove("hidden");
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

    const exportBtn = document.getElementById("exportReportBtn");
    const exportModal = document.getElementById("exportModal");
    const creatorInput = document.getElementById("creatorInput");
    const cancelExportBtn = document.getElementById("cancelExportBtn");
    const submitExportBtn = document.getElementById("submitExportBtn");

    if (exportBtn && exportModal) {
        // открыть модалку
        exportBtn.addEventListener("click", (e) => {
            e.preventDefault();
            creatorInput.value = "";
            submitExportBtn.disabled = true;

            document.getElementById("missingSections").classList.add("hidden"); // сброс

            exportModal.classList.remove("hidden");
        });

        // включать кнопку только если поле заполнено
        creatorInput.addEventListener("input", () => {
            submitExportBtn.disabled = creatorInput.value.trim() === "";
        });

        // закрыть модалку
        cancelExportBtn.addEventListener("click", () => {
            exportModal.classList.add("hidden");
        });

        // отправка
        submitExportBtn.addEventListener("click", async () => {
            const creator = creatorInput.value.trim();
            if (!creator) return;

            submitExportBtn.disabled = true;

            try {
                const response = await apiRequest("/api/v1/reports/export", {
                    method: "POST",
                    body: JSON.stringify({ creator: creator })
                });

                if (!response.ok) {
                    showToast("Ошибка экспорта", "error");
                    submitExportBtn.disabled = false;
                    return;
                }

                const data = await response.json();
                const missing = Array.isArray(data.missing) ? data.missing : [];

                // base64 -> Blob
                const bytes = Uint8Array.from(atob(data.file), c => c.charCodeAt(0));
                const blob = new Blob([bytes], {
                    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                });

                const now = new Date();
                const dd = String(now.getDate()).padStart(2, "0");
                const mm = String(now.getMonth() + 1).padStart(2, "0");
                const yyyy = now.getFullYear();
                const dateStr = `${dd}.${mm}.${yyyy}`;
                const filename = `Строевая записка ${dateStr}.xlsx`;

                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);

                showToast("Записка экспортирована", "success");
                submitExportBtn.disabled = false;

                if (missing.length) {
                    showMissingSections(missing);          // окно оставляем открытым
                } else {
                    document.getElementById("missingSections").classList.add("hidden");
                    exportModal.classList.add("hidden");
                }
            } catch (err) {
                console.error(err);
                showToast("Ошибка соединения", "error");
                submitExportBtn.disabled = false;
            }
        });
    }
});