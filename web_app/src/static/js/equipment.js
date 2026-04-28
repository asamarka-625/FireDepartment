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
            status: status.toLowerCase(),
            maintenance: note && date ? {
                note: note,
                date: date
            } : null
        };

        try {
            const response = await apiRequest("/api/v1/machinery/update", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                // обновляем отображение
                row.querySelector(".status-text").textContent = status;

                const viewBlock = row.querySelector("td:nth-child(6) .view");
                if (payload.maintenance) {
                    viewBlock.innerHTML = `
                        <div>${payload.maintenance.note}</div>
                        <div>${payload.maintenance.date}</div>
                    `;
                } else {
                    viewBlock.innerHTML = `<span class="no-maintenance">Нет</span>`;
                }

                cancelBtn.click(); // выйти из режима редактирования
            } else {
                alert("Ошибка сохранения");
            }
        } catch (e) {
            console.error(e);
            alert("Ошибка");
        }
    });

    const createBtn = document.getElementById("createReportBtn");
    const sectionId = createBtn.dataset.section;

    createBtn.addEventListener("click", async () => {
        if (createBtn.disabled) return;

        createBtn.disabled = true;
        createBtn.textContent = "Создание...";

        try {
            const response = await apiRequest(`/api/v1/reports/create/${sectionId}`, {
                method: "POST"
            });

            if (response.ok) {
                createBtn.textContent = "✔ Записка создана";
                showToast("Записка успешно создана", "success");
            }
            else {
                showToast("Ошибка при создании записки", "error");
                createBtn.disabled = false;
                createBtn.textContent = "Создать строевую записку";
            }

        } catch (e) {
            console.error(e);
            showToast("Ошибка соединения", "error");

            createBtn.disabled = false;
            createBtn.textContent = "Создать строевую записку";
        }
    });
});