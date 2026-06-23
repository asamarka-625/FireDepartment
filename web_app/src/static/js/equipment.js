document.querySelectorAll("tr[data-id]").forEach(row => {
    const editBtn = row.querySelector(".edit-btn");
    const saveBtn = row.querySelector(".save-btn");
    const cancelBtn = row.querySelector(".cancel-btn");

    const viewElements = row.querySelectorAll(".view");
    const editElements = row.querySelectorAll(".edit");

    // включить режим редактирования
    editBtn.addEventListener("click", () => {
        viewElements.forEach(el => el.classList.add("hidden"));
        editElements.forEach(el => el.classList.remove("hidden"));

        editBtn.classList.add("hidden");
        saveBtn.classList.remove("hidden");
        cancelBtn.classList.remove("hidden");
    });

    // отмена
    cancelBtn.addEventListener("click", () => {
        viewElements.forEach(el => el.classList.remove("hidden"));
        editElements.forEach(el => el.classList.add("hidden"));

        editBtn.classList.remove("hidden");
        saveBtn.classList.add("hidden");
        cancelBtn.classList.add("hidden");

        row.querySelector(".maintenance-note").value = "";
        row.querySelector(".maintenance-date").value = "";
    });

    // сохранение
    saveBtn.addEventListener("click", async () => {
        const id = row.dataset.id;
        const status = row.querySelector(".status-select").value;
        const note = row.querySelector(".maintenance-note").value;
        const date = row.querySelector(".maintenance-date").value;

        const operational = row.querySelector(".operational-input").value === "true";

        const supervisor = row.querySelector(".supervisor-input").value;
        const currentPersonnel = Number(row.querySelector(".current-personnel-input").value);
        const gdzs = Number(row.querySelector(".gdzs-input").value);

        if (date && !note) {
            showToast("Дата не может быть указана без причины", "error");
            return;
        }

        if (note && !date) {
            showToast("Причина не может быть указана без даты", "error");
            return;
        }

        const payload = {
            id: Number(id),
            operational: operational,
            supervisor: supervisor,
            current_personnel: currentPersonnel,
            gdzs: gdzs,
            status: status.toLowerCase(),

            maintenance: note && date ? { note: note, date: date } : null
        };

        try {
            const response = await apiRequest("/api/v1/machinery/update", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                row.querySelector(".operational-text").textContent =
                    operational ? "Да" : "Нет";
                row.querySelector(".supervisor-text").textContent = supervisor;
                row.querySelector(".current-personnel-text").textContent = currentPersonnel;
                row.querySelector(".gdzs-text").textContent = gdzs;
                row.querySelector(".status-text").textContent = status;

                const viewBlock = row.querySelector(".maintenance");
                if (payload.maintenance) {
                    viewBlock.innerHTML = `
                        <div>${payload.maintenance.note}</div>
                        <div>${payload.maintenance.date}</div>
                    `;
                }

                cancelBtn.click();
            } else {
                alert("Ошибка сохранения");
            }
        } catch (e) {
            console.error(e);
            alert("Ошибка");
        }
    });
});   // <-- цикл по строкам ЗАКРЫВАЕТСЯ здесь


// ===== Логика модалки — навешивается ОДИН раз, вне цикла =====
const createBtn       = document.getElementById("createReportBtn");
const reportModal     = document.getElementById("reportModal");
const leadershipInput = document.getElementById("leadershipInput");
const cancelReportBtn = document.getElementById("cancelReportBtn");
const submitReportBtn = document.getElementById("submitReportBtn");
const sectionId       = createBtn.dataset.section;

const staffInput   = document.getElementById("personnelStaffInput");
const listInput    = document.getElementById("personnelListInput");
const presentInput = document.getElementById("personnelPresentInput");

// число >= 0 и не пустое
const isValidCount = (v) =>
    v.trim() !== "" && Number.isFinite(Number(v)) && Number(v) >= 0;

function validateReportForm() {
    const ok =
        leadershipInput.value.trim() !== "" &&
        isValidCount(staffInput.value) &&
        isValidCount(listInput.value) &&
        isValidCount(presentInput.value);

    submitReportBtn.disabled = !ok;
}

// открыть modal — сброс всех полей
createBtn.addEventListener("click", () => {
    leadershipInput.value = "";
    staffInput.value   = "";
    listInput.value    = "";
    presentInput.value = "";
    submitReportBtn.disabled = true;
    reportModal.classList.remove("hidden");
});

// единая валидация на изменение любого поля
[leadershipInput, staffInput, listInput, presentInput]
    .forEach(el => el.addEventListener("input", validateReportForm));

// закрыть modal
cancelReportBtn.addEventListener("click", () => {
    reportModal.classList.add("hidden");
});

// отправка
submitReportBtn.addEventListener("click", async () => {
    const leadership = leadershipInput.value.trim();

    const personnelStaff   = Number(staffInput.value);
    const personnelList    = Number(listInput.value);
    const personnelPresent = Number(presentInput.value);

    // защита от ручного ввода минуса / пустых значений
    if (!leadership ||
        ![personnelStaff, personnelList, personnelPresent]
            .every(n => Number.isFinite(n) && n >= 0)) {
        showToast("Заполните все поля корректными числами (не меньше 0)", "error");
        return;
    }

    submitReportBtn.disabled = true;

    try {
        const response = await apiRequest("/api/v1/reports/create", {
            method: "POST",
            body: JSON.stringify({
                section_id: Number(sectionId),
                leadership: leadership,
                total_personnel: personnelStaff,     // по штату
                personnel: personnelList,       // по списку
                current_personnel: personnelPresent  // на лицо
            })
        });

        if (response.ok) {
            reportModal.classList.add("hidden");
            createBtn.textContent = "✔ Записка создана";
            createBtn.disabled = true;
            showToast("Записка успешно создана", "success");
        } else {
            submitReportBtn.disabled = false;
            showToast("Ошибка при создании записки", "error");
        }
    } catch (e) {
        console.error(e);
        submitReportBtn.disabled = false;
        showToast("Ошибка соединения", "error");
    }
});