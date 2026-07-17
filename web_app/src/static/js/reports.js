const container = document.getElementById("reportsContainer");
const loadMoreBtn = document.getElementById("loadMoreBtn");

const sectionId = container.dataset.section;

let lastSeenId = null;
const PAGE_SIZE = 10;
let isLoading = false;

function hasAdjacentUppercase(text) {
    if (!text) return false;
    for (let i = 0; i < text.length - 1; i++) {
        const a = text[i];
        const b = text[i + 1];
        const aUpper = a !== a.toLowerCase() && a === a.toUpperCase();
        const bUpper = b !== b.toLowerCase() && b === b.toUpperCase();
        if (aUpper && bUpper) return true;
    }
    return false;
}

async function loadReports() {
    if (isLoading) return;
    isLoading = true;

    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = "Загрузка...";

    try {
        let url = `/api/v1/reports/${sectionId}?reports_per_page=${PAGE_SIZE}`;
        if (lastSeenId) {
            url += `&last_seen_id=${lastSeenId}`;
        }

        const response = await apiRequest(url);

        if (!response.ok) {
            showToast("Ошибка загрузки записок", "error");
            return;
        }

        const data = await response.json();

        if (data.length === 0) {
            loadMoreBtn.textContent = "Больше нет записок";
            return;
        }

        data.forEach(report => {
            container.appendChild(createReportCard(report));
        });

        lastSeenId = data[data.length - 1].id;

        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = "Загрузить ещё";

    } catch (e) {
        console.error(e);
        showToast("Ошибка соединения", "error");
    }

    isLoading = false;
}

function createReportCard(report) {
    const card = document.createElement("div");
    card.className = "report-card";

    const sortedMachinery = [...report.machinery].sort(
        (a, b) =>
            (hasAdjacentUppercase(a.title) ? 0 : 1) -
            (hasAdjacentUppercase(b.title) ? 0 : 1)
    );

    const machinesRows = sortedMachinery.map(m => {
        let maintenance = "—";

        if (m.maintenance) {
            const rawDate = m.maintenance.date;
            const date = rawDate
                ? new Date(rawDate).toLocaleDateString("ru-RU")
                : "";

            maintenance = `
                <div class="maintenance-block">
                    <div>${m.maintenance.note}</div>
                    ${date ? `<div class="maintenance-date">${date}</div>` : ""}
                </div>
            `;
        }

        return `
            <tr>
                <td>${m.title}</td>
                <td>${m.model || "-"}</td>
                <td>${m.number || "-"}</td>
                <td>${m.supervisor || "-"}</td>
                <td>${m.current_personnel ?? 0}</td>
                <td>${m.gdzs ?? 0}</td>
                <td>${m.status}</td>
                <td>${maintenance}</td>
            </tr>
        `;
    }).join("");

    // ---- сводка по записке (личный состав уровня подразделения) ----
    const staff   = report.total_personnel ?? 0;  // по штату
    const list    = report.personnel ?? 0;  // по списку
    const present = report.current_personnel ?? 0;  // на лицо
    const absent  = Math.max(list - present, 0);    // отсутствует
    const operational_machinery = report.operational_machinery; // оперативная машина

    const summaryBlock = `
        <div class="report-summary">
            <div class="summary-item">
                <span class="summary-label">По штату:</span>
                <span class="summary-value">${staff}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">По списку:</span>
                <span class="summary-value">${list}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">На лицо:</span>
                <span class="summary-value">${present}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Отсутствует:</span>
                <span class="summary-value">${absent}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Оперативная машина:</span>
                <span class="summary-value">${operational_machinery ? "Да" : "Нет"}</span>
            </div>
        </div>
    `;

    card.innerHTML = `
        <div class="report-header clickable">
            <div class="report-left">
                <div class="report-id">№${report.id}</div>
                <div class="report-section-badge">${report.section}</div>
            </div>

            <div class="report-right">
                <div class="report-leadership">
                    Ответственный: ${report.leadership || "-"}
                </div>

                <div class="report-date">
                    ${report.date}
                </div>

                <div class="arrow">▼</div>
            </div>
        </div>

        <div class="report-body hidden">
            ${summaryBlock}

            <div class="report-table-wrapper">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Название</th>
                            <th>Модель</th>
                            <th>Номер</th>
                            <th>Старший</th>
                            <th>Личный состав</th>
                            <th>ГДЗС</th>
                            <th>Статус</th>
                            <th>Обслуживание</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${machinesRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    const header = card.querySelector(".report-header");
    const body = card.querySelector(".report-body");

    header.addEventListener("click", () => {
        const isOpen = !body.classList.contains("hidden");

        body.classList.toggle("hidden");
        card.classList.toggle("open", !isOpen);
    });

    return card;
}

document.addEventListener("DOMContentLoaded", () => {
    // первая загрузка
    loadMoreBtn.addEventListener("click", loadReports);
    loadReports();
});