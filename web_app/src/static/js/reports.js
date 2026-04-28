const container = document.getElementById("reportsContainer");
const loadMoreBtn = document.getElementById("loadMoreBtn");

const sectionId = container.dataset.section;

let lastSeenId = null;
const PAGE_SIZE = 10;
let isLoading = false;

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

    const machinesRows = report.machinery.map(m => {
        let maintenance = "—";

        if (m.maintenance) {
            const date = new Date(m.maintenance.date)
                .toLocaleDateString("ru-RU");

            maintenance = `
                <div class="maintenance-block">
                    <div>${m.maintenance.note}</div>
                    <div class="maintenance-date">${date}</div>
                </div>
            `;
        }

        return `
            <tr>
                <td>${m.title}</td>
                <td>${m.model || "-"}</td>
                <td>${m.number || "-"}</td>
                <td>${m.status}</td>
                <td>${maintenance}</td>
            </tr>
        `;
    }).join("");

    card.innerHTML = `
        <div class="report-header clickable">
            <div class="report-left">
                <div class="report-id">№${report.id}</div>
                <div class="report-section-badge">${report.section}</div>
            </div>

            <div class="report-right">
                <div class="report-date">${report.date}</div>
                <div class="arrow">▼</div>
            </div>
        </div>

        <div class="report-body hidden">
            <div class="report-table-wrapper">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Название</th>
                            <th>Модель</th>
                            <th>Номер</th>
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
    const arrow = card.querySelector(".arrow");

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