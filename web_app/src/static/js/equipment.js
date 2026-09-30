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

        // возвращаем исходные значения из карточки (а не очищаем: иначе следующее сохранение сняло бы обслуживание)
        const noteInput = row.querySelector(".maintenance-note");
        const dateInput = row.querySelector(".maintenance-date");
        if (noteInput) noteInput.value = noteInput.defaultValue;
        if (dateInput) dateInput.value = dateInput.defaultValue;

        row.querySelectorAll(".supervisor-input, .current-personnel-input, .gdzs-input, .departure-order-input").forEach(input => {
            input.value = input.defaultValue;
        });

        const statusSelect = row.querySelector(".status-select");
        if (statusSelect) statusSelect.value = statusSelect.dataset.original;
    });

    // сохранение
    saveBtn.addEventListener("click", async () => {
        const id = row.dataset.id;
        // принятая по передислокации машина: правится только расчёт (старший, личный состав, ГДЗС)
        const crewOnly = row.dataset.crewOnly === "1";
        const statusSelect = row.querySelector(".status-select");
        const status = statusSelect ? statusSelect.value : row.querySelector(".status-text").textContent.trim();
        const noteInput = row.querySelector(".maintenance-note");
        const dateInput = row.querySelector(".maintenance-date");
        const note = noteInput ? noteInput.value : "";
        const date = dateInput ? dateInput.value : "";

        const supervisor = row.querySelector(".supervisor-input").value;
        const currentPersonnel = Number(row.querySelector(".current-personnel-input").value);
        const gdzs = Number(row.querySelector(".gdzs-input").value);

        // ход выезда: только у АЦ штатной ПСЧ (поле есть в строке)
        const orderInput = row.querySelector(".departure-order-input");
        const departureOrder = orderInput && orderInput.value.trim() !== "" ? Number(orderInput.value) : null;
        if (orderInput && departureOrder !== null && (!Number.isInteger(departureOrder) || departureOrder < 1)) {
            showToast("Ход выезда — целое число не меньше 1", "error");
            return;
        }

        if (date && !note) {
            showToast("Дата не может быть указана без причины", "error");
            return;
        }

       const payload = {
            id: Number(id),
            supervisor: supervisor,
            current_personnel: currentPersonnel,
            gdzs: gdzs,
            status: status.toLowerCase(),

            // причина может быть без даты
            maintenance: note ? { note: note, date: date || null } : null
        };
        if (orderInput) {
            payload.departure_order = departureOrder;
        }

        try {
            const response = await apiRequest("/api/v1/machinery/update", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                // новые значения становятся «исходными» для следующей отмены
                row.querySelector(".supervisor-input").defaultValue = supervisor;
                row.querySelector(".current-personnel-input").defaultValue = currentPersonnel;
                row.querySelector(".gdzs-input").defaultValue = gdzs;
                if (statusSelect) statusSelect.dataset.original = status;

                if (orderInput) {
                    orderInput.defaultValue = departureOrder === null ? "" : departureOrder;
                    row.querySelector(".departure-order-text").textContent = departureOrder === null ? "—" : departureOrder;

                    // подпись в записке: АЦ + ход
                    const short = row.dataset.shortTitle;
                    row.querySelector(".label-text").textContent =
                        departureOrder === null ? short : `${short}-${departureOrder}`;
                }
                if (noteInput) noteInput.defaultValue = note;
                if (dateInput) dateInput.defaultValue = date;

                row.querySelector(".supervisor-text").textContent = supervisor;
                row.querySelector(".current-personnel-text").textContent = currentPersonnel;
                row.querySelector(".gdzs-text").textContent = gdzs;
                row.querySelector(".status-text").textContent = status;

                const viewBlock = row.querySelector(".maintenance");
                if (crewOnly) {
                    // обслуживание не менялось
                } else if (payload.maintenance) {
                    viewBlock.innerHTML = `
                        <div>${payload.maintenance.note}</div>
                        ${payload.maintenance.date ? `<div>${payload.maintenance.date}</div>` : ""}
                    `;
                } else {
                    viewBlock.innerHTML = `<span class="no-maintenance">Нет</span>`;
                }

                cancelBtn.click();
            } else {
                showToast(await errorMessage(response, "Ошибка сохранения"), "error");
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
const operationalMachineryInput = document.getElementById("operationalMachineryInput");
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
    operationalMachineryInput.checked = false;
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
                current_personnel: personnelPresent,  // на лицо
                operational_machinery: operationalMachineryInput.checked
            })
        });

        if (response.ok) {
            reportModal.classList.add("hidden");
            // повторная подача за сутки перезаписывает предыдущую — кнопка остаётся доступной
            createBtn.textContent = "✔ Записка подана (обновить)";
            const banner = document.getElementById("relocationBanner");
            if (banner) banner.remove();
            showToast("Записка успешно создана", "success");
        } else {
            submitReportBtn.disabled = false;
            showToast(await errorMessage(response, "Ошибка при создании записки"), "error");
        }
    } catch (e) {
        console.error(e);
        submitReportBtn.disabled = false;
        showToast("Ошибка соединения", "error");
    }
});


// ===== Передислокация техники =====
const relocationModal      = document.getElementById("relocationModal");
const relocationTitle      = document.getElementById("relocationTitle");
const relocationTarget     = document.getElementById("relocationTarget");
const relocationReturnDate = document.getElementById("relocationReturnDate");
let relocationMachineryId  = null;

// дата возврата — не раньше завтрашнего дня
function setMinReturnDate() {
    const t = new Date();
    t.setDate(t.getDate() + 1);
    const pad = n => String(n).padStart(2, "0");
    relocationReturnDate.min = `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())}`;
}

document.querySelectorAll(".relocate-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        relocationMachineryId = Number(btn.dataset.machineryId);
        relocationTitle.textContent = btn.dataset.title;
        relocationReturnDate.value = "";
        setMinReturnDate();
        relocationModal.classList.remove("hidden");
    });
});

document.getElementById("cancelRelocationBtn").addEventListener("click", () => {
    relocationModal.classList.add("hidden");
});

document.getElementById("submitRelocationBtn").addEventListener("click", async () => {
    const submitBtn = document.getElementById("submitRelocationBtn");
    submitBtn.disabled = true;

    try {
        const response = await apiRequest("/api/v1/relocations/create", {
            method: "POST",
            body: JSON.stringify({
                machinery_id: relocationMachineryId,
                to_section_id: Number(relocationTarget.value),
                date_return: relocationReturnDate.value || null
            })
        });

        if (response.ok) {
            showToast("Передислокация оформлена", "success");
            setTimeout(() => window.location.reload(), 600);
        } else {
            showToast(await errorMessage(response, "Не удалось оформить передислокацию"), "error");
            submitBtn.disabled = false;
        }
    } catch (e) {
        console.error(e);
        showToast("Ошибка соединения", "error");
        submitBtn.disabled = false;
    }
});

// изменение даты возврата (дата не позже сегодняшней = отмена) и отмена передислокации
document.querySelectorAll("tr[data-relocated-id]").forEach(row => {
    const machineryId = Number(row.dataset.relocatedId);

    async function send(url, body) {
        try {
            const response = await apiRequest(url, { method: "POST", body: JSON.stringify(body) });

            if (response.ok) {
                window.location.reload();
            } else {
                showToast(await errorMessage(response, "Ошибка"), "error");
            }
        } catch (e) {
            console.error(e);
            showToast("Ошибка соединения", "error");
        }
    }

    row.querySelector(".relocation-save-btn").addEventListener("click", () => {
        send("/api/v1/relocations/update", {
            machinery_id: machineryId,
            date_return: row.querySelector(".relocation-return-date").value || null
        });
    });

    row.querySelector(".relocation-cancel-btn").addEventListener("click", () => {
        send("/api/v1/relocations/cancel", { machinery_id: machineryId });
    });
});