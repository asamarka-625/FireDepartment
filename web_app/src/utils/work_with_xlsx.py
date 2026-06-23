# Внешние зависимости
from typing import Literal, Any, List
import datetime
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
# Внутренние модули
from web_app.src.core import cfg
from web_app.src.schemas import ReportScheme


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
            "green": PatternFill(start_color="92D050", end_color="92D050", fill_type="solid"),
            "red": PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
        }

    def create_cell(
        self,
        coordinate: str,
        value: Any,
        color_fill: Literal["none", "green", "red"] = "none",
        title_font: bool = False
    ):
        self.ws[coordinate].value = value
        self.ws[coordinate].font = self.title_font if title_font else self.font
        self.ws[coordinate].fill = self.fills.get(color_fill, PatternFill(fill_type=None))
        self.ws[coordinate].border = self.border
        self.ws[coordinate].alignment = self.alignment
        self.ws[coordinate].number_format = self.number_format

    # Создаем строку с данными ПСЧ. Возвращает номер последней занятой строки.
    def create_section(
        self,
        section_num: int,
        start_row: int,
        report: ReportScheme
    ) -> int:
        machines = [
            {
                "title": m.title,
                "status": m.status,
                "operational": "Да" if m.operational else "Нет",
                "current_personnel": m.current_personnel,
                "gdzs": m.gdzs,
                "supervisor": m.supervisor
            }
            for m in report.machinery
        ]

        section_report = {
            "section_title": report.section,
            "total_personnel": report.total_personnel,
            "personnel": report.personnel,
            "active_personnel": report.current_personnel,
            "inactive_personnel_percent": round(
                ((report.personnel - report.current_personnel) * 100) / report.personnel, 2
            ) if report.personnel > 0 else 100,
            "active_personal_machines": sum(m["current_personnel"] for m in machines if m["status"] == "Включено"),
            "leadership": report.leadership
        }
        section_report_keys = tuple(section_report.keys())

        len_row = len(machines)
        end_row = start_row + len_row - 1
        columns_for_merge_start = ("A", "B", "D", "E", "F", "G", "M", "O")
        columns_for_merge_end = ("A", "C", "D", "E", "F", "G", "M", "P")

        for i, (column_start, column_end) in enumerate(zip(columns_for_merge_start, columns_for_merge_end)):
            self.ws.merge_cells(f"{column_start}{start_row}:{column_end}{end_row}")
            title_font = False

            if i == 0:
                value = section_num
            else:
                value = section_report[section_report_keys[i - 1]]
                if i == 1:
                    value = value.upper()
                    title_font = True

            self.create_cell(f"{column_start}{start_row}", value, title_font=title_font)

        for i, machine in enumerate(machines):
            row = start_row + i

            self.create_cell(f"H{row}", machine["title"])
            self.create_cell(f"I{row}", machine["operational"])

            current_personnel_color: Literal["none", "green", "red"] = "none"
            if machine["status"] == "включено":
                current_personnel = machine["current_personnel"]
            else:
                current_personnel = machine["status"].upper()

                if machine["status"] in ("резерв", "резерв (лсо)"):
                    current_personnel_color = "green"
                elif machine["status"] == "ремонт":
                    current_personnel_color = "red"

            self.create_cell(f"J{row}", current_personnel, color_fill=current_personnel_color)
            self.ws.merge_cells(f"K{row}:L{row}")
            self.create_cell(f"K{row}", machine["supervisor"])
            self.create_cell(f"N{row}", machine["gdzs"])

        return end_row

    # Возвращает готовый xlsx в памяти, не сохраняя на диск
    def run(
        self,
        reports: List[ReportScheme],
        creator: str
    ) -> BytesIO:
        now = datetime.datetime.now()

        hours = now.strftime('%H')
        minutes = now.strftime('%M')

        day = now.strftime('%d')
        month = MONTHS_RU[now.month]
        year = now.strftime('%Y')

        self.create_cell("A2", f"На {hours} часов {minutes} минут", title_font=True)
        self.create_cell("E2", day, title_font=True)
        self.create_cell("H2", month, title_font=True)
        self.create_cell("K2", year, title_font=True)

        start_row = 6  # первая строка под данные (после шапки)

        for i, report in enumerate(reports):
            end_row = self.create_section(
                section_num=i + 1,
                start_row=start_row,
                report=report
            )
            start_row = end_row + 1  # следующая секция — сразу под текущей

        self.ws.merge_cells(f"A{start_row}:B{start_row}")
        self.ws.merge_cells(f"C{start_row}:N{start_row}")
        self.ws.merge_cells(f"O{start_row}:P{start_row}")

        self.create_cell(f"A{start_row}", "Строевую записку подготовил")
        self.create_cell(f"C{start_row}", "")
        self.create_cell(f"O{start_row}", creator)

        buffer = BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        return buffer