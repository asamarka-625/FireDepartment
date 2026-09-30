# Внешние зависимости
from typing import Literal, Any, List, Dict, Optional, TYPE_CHECKING
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
# Внутренние модули
from web_app.src.core import cfg
from web_app.src.utils.sorting import sort_machinery, is_special, machinery_sort_key
from web_app.src.utils.machinery_rules import machinery_label

if TYPE_CHECKING:
    # Только для аннотаций (schemas импортируют utils.machinery_rules — избегаем циклического импорта)
    from web_app.src.schemas import ReportScheme, MachineryScheme


MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


class ReportExelCreator:
    def __init__(self):
        self.wb = load_workbook(f"{cfg.TEMPLATE_NAME}.xlsx")
        self.ws = self.wb.active

        self.font = Font(name="Times New Roman", size=12, bold=False, italic=False)
        self.title_font = Font(name="Times New Roman", size=12, bold=True, italic=False)

        thin = Side(style="thin")
        self.border = Border(left=thin, right=thin, top=thin, bottom=thin)

        self.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.number_format = "General"

        self.fills = {
            "none": PatternFill(fill_type=None),
            "green": PatternFill(start_color="C8E7A8", end_color="C8E7A8", fill_type="solid"),
            "red": PatternFill(start_color="FF8080", end_color="FF8080", fill_type="solid"),
            "yellow": PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid"),
        }

    def create_cell(
        self,
        coordinate: str,
        value: Any,
        color_fill: Literal["none", "green", "red", "yellow"] = "none",
        title_font: bool = False
    ):
        self.ws[coordinate].value = value
        self.ws[coordinate].font = self.title_font if title_font else self.font
        self.ws[coordinate].fill = self.fills.get(color_fill, PatternFill(fill_type=None))
        self.ws[coordinate].border = self.border
        self.ws[coordinate].alignment = self.alignment
        self.ws[coordinate].number_format = self.number_format

    def create_merged_cell(
        self,
        cell_range: str,
        value: Any,
        color_fill: Literal["none", "green", "red", "yellow"] = "none",
        title_font: bool = False
    ):
        self.ws.merge_cells(cell_range)

        font = self.title_font if title_font else self.font
        fill = self.fills.get(color_fill, PatternFill(fill_type=None))

        for row in self.ws[cell_range]:
            for cell in row:
                cell.font = font
                cell.fill = fill
                cell.border = self.border
                cell.alignment = self.alignment
                cell.number_format = self.number_format

        top_left = cell_range.split(":")[0]
        self.ws[top_left].value = value

    # Цвет/значение по состоянию машины
    @staticmethod
    def _status_color(status: str) -> Literal["none", "green", "red", "yellow"]:
        status_lower = status.lower()

        if status_lower == "включено":
            return "none"

        if status_lower in ("резерв", "резерв (лсо)", "резерв (лсб)"):
            return "green"

        return "red"

    # Техника ПСЧ для листа «Строевая записка»: только специальная (п. 1.4 / 2.3), отсортированная по типу (п. 2.7)
    @staticmethod
    def _special_machinery(report: "ReportScheme") -> List["MachineryScheme"]:
        return sort_machinery([m for m in report.machinery if is_special(m.kind, m.title)])

    # Создаем строку с данными ПСЧ. Возвращает номер последней занятой строки.
    def create_section(
        self,
        section_num: int,
        start_row: int,
        report: "ReportScheme"
    ) -> int:
        machines = []
        for m in self._special_machinery(report):
            relocation = m.relocation
            given_away = relocation is not None and relocation.direction == "out"
            received = relocation is not None and relocation.direction == "in"

            # Подпись собирается здесь, в момент формирования отчёта: АЦ-1, АЦ-2, АЛ, АКП...
            title = m.label
            if received:
                title = f"{title} (из {relocation.partner})"

            machines.append({
                "title": title,
                "status": m.status,
                "current_personnel": m.current_personnel,
                "gdzs": m.gdzs,
                "supervisor": m.supervisor,
                "given_away": given_away,
                "partner": relocation.partner if relocation else None,
            })

        len_row = max(len(machines), 1)  # у ПСЧ без специальной техники всё равно нужна одна строка
        end_row = start_row + len_row - 1

        inactive_percent = round(
            ((report.personnel - report.current_personnel) * 100) / report.personnel, 2
        ) if report.personnel > 0 else 100

        # Колонка «Всего»: машина, ушедшая в передислокацию, в боевом расчёте отдающей ПСЧ не участвует,
        # у принимающей — считается со своим сегодняшним расчётом
        active_personal_machines = sum(
            m["current_personnel"] for m in machines
            if m["status"].lower() == "включено" and not m["given_away"]
        )

        operational_value = "Да" if report.operational_machinery else "Нет"

        # --- Общие для отделения ячейки (объединяем по вертикали на все машины) ---
        section_cells = [
            ("A", "A", section_num, False),
            ("B", "C", report.section.upper(), True),
            ("D", "D", report.total_personnel, False),    # По штату
            ("E", "E", report.personnel, False),          # По списку
            ("F", "F", report.current_personnel, False),  # На лицо
            ("G", "G", f"{inactive_percent}%", False),    # Отсутствуют
            ("M", "M", active_personal_machines, False),  # Всего
            ("N", "O", operational_value, False),         # Оперативная машина (общая)
            ("P", "Q", report.leadership, False),         # Руководство караула
        ]

        for col_start, col_end, value, is_title in section_cells:
            self.create_merged_cell(
                cell_range=f"{col_start}{start_row}:{col_end}{end_row}",
                value=value,
                title_font=is_title
            )

        if not machines:
            self.create_cell(f"H{start_row}", "—")
            self.create_cell(f"I{start_row}", "")
            self.create_cell(f"J{start_row}", "")
            self.create_merged_cell(cell_range=f"K{start_row}:L{start_row}", value="")
            return end_row

        # --- Данные по каждой машине ---
        for i, machine in enumerate(machines):
            row = start_row + i

            self.create_cell(f"H{row}", machine["title"])   # Техника

            personnel_color: Literal["none", "green", "red", "yellow"] = "none"

            if machine["given_away"]:
                # Передислоцирована в другую ПСЧ: отдельная строка, в расчёт не идёт (как «Ремонт»)
                personnel_value = f"ПЕРЕДИСЛОКАЦИЯ → {machine['partner']}".upper()
                personnel_color = "yellow"
                gdzs_value = ""
                supervisor_value = ""

            elif machine["status"].lower() == "включено":
                personnel_value = machine["current_personnel"]
                gdzs_value = machine["gdzs"]
                supervisor_value = machine["supervisor"]

            else:
                personnel_value = machine["status"].upper()
                personnel_color = self._status_color(machine["status"])
                gdzs_value = machine["gdzs"]
                supervisor_value = machine["supervisor"]

            self.create_cell(f"I{row}", personnel_value, color_fill=personnel_color)  # Личный состав
            self.create_cell(f"J{row}", gdzs_value)                                   # ГДЗС

            self.create_merged_cell(
                cell_range=f"K{row}:L{row}",
                value=supervisor_value
            ) # Старший на машине

        return end_row

    # Возвращает готовый xlsx в памяти, не сохраняя на диск
    def run(
        self,
        reports: List["ReportScheme"],
        machineries: List[dict],
        creator: str
    ) -> BytesIO:
        # свежая книга на каждый экспорт (иначе singleton копит листы/строки)
        self.wb = load_workbook(f"{cfg.TEMPLATE_NAME}.xlsx")

        # активный лист шаблона -> строевая записка (2-й лист)
        report_ws = self.wb.active
        report_ws.title = "Строевая записка"
        self.ws = report_ws
        self._fill_report(reports, creator)

        # новый лист с техникой -> ставим первым
        machines_ws = self.wb.create_sheet("Техника", 0)
        self.ws = machines_ws
        self._fill_machineries(machineries)

        # сводка по типам техники -> последний лист
        summary_ws = self.wb.create_sheet("Сводка по технике")
        self.ws = summary_ws
        self._fill_type_summary(reports)

        # файл открывается на листе с техникой
        self.wb.active = 0

        buffer = BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        return buffer

    def _fill_report(
        self,
        reports: List["ReportScheme"],
        creator: str
    ) -> None:
        now = datetime.now(ZoneInfo("Europe/Moscow"))

        hours = now.strftime('%H')
        minutes = now.strftime('%M')

        day = now.strftime('%d')
        month = MONTHS_RU[now.month]
        year = now.strftime('%Y')

        self.create_cell("A2", f"На {hours} часов {minutes} минут", title_font=True)
        self.create_cell("E2", day, title_font=True)
        self.create_cell("H2", month, title_font=True)
        self.create_cell("K2", year, title_font=True)

        # Номер караула в шапке не выводится (п. 1.3): убираем подпись «(караул)» из шаблона
        self.ws["N3"].value = None

        # Колонка «Личный состав» вмещает подпись «Передислокация → ПСЧ-…»
        self.ws.column_dimensions["I"].width = max(self.ws.column_dimensions["I"].width or 0, 22)

        start_row = 6  # первая строка под данные (после шапки)

        for i, report in enumerate(reports):
            end_row = self.create_section(
                section_num=i + 1,
                start_row=start_row,
                report=report
            )
            start_row = end_row + 1  # следующая секция — сразу под текущей

        start_row = self._fill_report_totals(reports, start_row)

        self.create_merged_cell(
            cell_range=f"A{start_row}:B{start_row}",
            value="Строевую записку подготовил"
        )
        self.create_merged_cell(
            cell_range=f"C{start_row}:N{start_row}",
            value=""
        )
        self.create_merged_cell(
            cell_range=f"O{start_row}:Q{start_row}",
            value=creator
        )

    # Итоговая строка: общая численность личного состава и количество техники по всем подавшим ПСЧ (п. 2.8).
    # Возвращает номер следующей свободной строки.
    def _fill_report_totals(
        self,
        reports: List["ReportScheme"],
        row: int
    ) -> int:
        total_staff = sum(r.total_personnel for r in reports)
        total_list = sum(r.personnel for r in reports)
        total_present = sum(r.current_personnel for r in reports)
        inactive_percent = round(
            ((total_list - total_present) * 100) / total_list, 2
        ) if total_list > 0 else 100

        machinery = self._unique_special_machinery(reports)
        machinery_total = len(machinery)
        machinery_on_duty = sum(
            1 for m in machinery
            if m.status.lower() == "включено" and not (m.relocation and m.relocation.direction == "out")
        )
        personnel_on_machines = sum(
            m.current_personnel for m in machinery
            if m.status.lower() == "включено" and not (m.relocation and m.relocation.direction == "out")
        )

        self.create_merged_cell(f"A{row}:C{row}", "ИТОГО", title_font=True)
        self.create_cell(f"D{row}", total_staff, title_font=True)
        self.create_cell(f"E{row}", total_list, title_font=True)
        self.create_cell(f"F{row}", total_present, title_font=True)
        self.create_cell(f"G{row}", f"{inactive_percent}%", title_font=True)
        self.create_merged_cell(
            f"H{row}:L{row}",
            f"Техники: {machinery_total} ед., в боевом расчёте: {machinery_on_duty}",
            title_font=True
        )
        self.create_cell(f"M{row}", personnel_on_machines, title_font=True)
        self.create_merged_cell(f"N{row}:Q{row}", "", title_font=True)

        return row + 1

    # Специальная техника всех записок без дублей: машина, переданная между ПСЧ, встречается в двух блоках
    # (у отдающей — «out», у принимающей — «in»). Считаем её один раз — по строке принимающей ПСЧ.
    @staticmethod
    def _unique_special_machinery(reports: List["ReportScheme"]) -> List["MachineryScheme"]:
        by_id: Dict[int, "MachineryScheme"] = {}

        for report in reports:
            for m in report.machinery:
                if not is_special(m.kind, m.title):
                    continue

                known = by_id.get(m.id)
                if known is None or (
                    known.relocation and known.relocation.direction == "out"
                    and not (m.relocation and m.relocation.direction == "out")
                ):
                    by_id[m.id] = m

        return list(by_id.values())

    # Сводка по типам техники (п. 2.8): единицы специальной техники в разбивке по типу и состоянию
    def _fill_type_summary(
        self,
        reports: List["ReportScheme"]
    ) -> None:
        headers = ["Тип техники", "Включено", "Резерв", "Не в боевом расчёте", "Всего"]
        cols = ["A", "B", "C", "D", "E"]

        for col, width in zip(cols, [28, 14, 14, 24, 14]):
            self.ws.column_dimensions[col].width = width

        for col, title in zip(cols, headers):
            self.create_cell(f"{col}1", title, title_font=True)

        self.ws.freeze_panes = "A2"

        # Тип: краткое обозначение (АЦ-1, АЦ-2... сводятся в «АЦ»), иначе полное название
        stats: Dict[str, Dict[str, int]] = {}

        for m in self._unique_special_machinery(reports):
            type_name = (m.short_title or "").strip().upper() or m.title
            item = stats.setdefault(type_name, {"on": 0, "reserve": 0, "other": 0})

            status_lower = m.status.lower()
            if m.relocation and m.relocation.direction == "out":
                item["other"] += 1
            elif status_lower == "включено":
                item["on"] += 1
            elif status_lower.startswith("резерв"):
                item["reserve"] += 1
            else:
                item["other"] += 1

        # Порядок: АЦ, АЛ, затем остальные по алфавиту
        def type_key(name: str):
            return (0 if name == "АЦ" else 1 if name == "АЛ" else 2, name)

        row = 2
        totals = {"on": 0, "reserve": 0, "other": 0}

        for type_name in sorted(stats, key=type_key):
            item = stats[type_name]
            total = item["on"] + item["reserve"] + item["other"]

            self.create_cell(f"A{row}", type_name)
            self.create_cell(f"B{row}", item["on"])
            self.create_cell(f"C{row}", item["reserve"])
            self.create_cell(f"D{row}", item["other"])
            self.create_cell(f"E{row}", total)

            for key in totals:
                totals[key] += item[key]

            row += 1

        self.create_cell(f"A{row}", "ИТОГО", title_font=True)
        self.create_cell(f"B{row}", totals["on"], title_font=True)
        self.create_cell(f"C{row}", totals["reserve"], title_font=True)
        self.create_cell(f"D{row}", totals["other"], title_font=True)
        self.create_cell(f"E{row}", sum(totals.values()), title_font=True)

    # Вся техника с обслуживанием (первый лист)
    def _fill_machineries(
        self,
        machineries: List[dict]
    ) -> None:
        headers = [
            "Подразделение", "Название", "Обозначение", "Ход выезда", "Модель", "Номер", "Статус",
            "Обслуживание", "Дата обслуживания", "Категория"
        ]
        cols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

        widths = {
            "A": 24, "B": 26, "C": 14, "D": 12, "E": 22, "F": 16,
            "G": 34, "H": 26, "I": 16, "J": 16
        }
        for col, width in widths.items():
            self.ws.column_dimensions[col].width = width

        for col, title in zip(cols, headers):
            self.create_cell(f"{col}1", title, title_font=True)

        self.ws.freeze_panes = "A2"

        if not machineries:
            return

        # Внутри ПСЧ: специальная — вверх; АЦ по ходу, АЛ, прочая
        machineries = sorted(
            machineries,
            key=lambda m: (
                m["section"],
                0 if is_special(m.get("kind"), m["title"]) else 1,
                machinery_sort_key(m["title"], m.get("short_title"), m.get("departure_order"))
            )
        )

        start_row = 2

        for idx, m in enumerate(machineries):
            row = start_row + idx

            # Статус: при передислокации машина остаётся в блоке штатной ПСЧ с пометкой (п. 3.6)
            if m.get("relocation_to"):
                since = m["relocation_from_date"]
                status_text = f"Передислокация → {m['relocation_to']}" + (
                    f" с {since.strftime('%d.%m.%Y')}" if since else ""
                )
                status_color: Literal["none", "green", "red", "yellow"] = "yellow"
            else:
                status_text = m["status"]
                status_color = self._status_color(m["status"])

            self.create_cell(f"B{row}", m["title"])
            # Обозначение как в строевой записке: АЦ-1, АЦ-2, АЛ...
            self.create_cell(
                f"C{row}",
                machinery_label(m["title"], m.get("short_title"), m.get("departure_order"))
            )
            self.create_cell(f"D{row}", m.get("departure_order") or "")  # ход выезда (у АЦ)
            self.create_cell(f"E{row}", m["model"] or "")
            self.create_cell(f"F{row}", m["number"] or "")
            self.create_cell(f"G{row}", status_text, color_fill=status_color)
            self.create_cell(f"H{row}", m["maintenance_note"] or "")

            date_val = m["maintenance_date"]
            self.create_cell(
                f"I{row}",
                date_val.strftime("%d.%m.%Y") if date_val else ""
            )
            self.create_cell(
                f"J{row}",
                "Специальная" if is_special(m.get("kind"), m["title"]) else "Прочая"
            )

        # объединяем "Подразделение" по группам подряд идущих машин
        group_start = start_row
        total = len(machineries)

        for idx in range(total):
            row = start_row + idx
            is_last = idx == total - 1
            next_section = None if is_last else machineries[idx + 1]["section"]

            if is_last or machineries[idx]["section"] != next_section:
                self.create_merged_cell(
                    f"A{group_start}:A{row}",
                    machineries[idx]["section"],
                    title_font=True
                )
                group_start = row + 1