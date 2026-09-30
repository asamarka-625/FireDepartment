# Внешние зависимости
from typing import List, Tuple, Optional, Sequence, FrozenSet
from datetime import date
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import Report, Machinery
from web_app.src.crud import sql_get_machineries
from web_app.src.schemas import ReportScheme, MachineryScheme
from web_app.src.utils.machinery_rules import today_msk
from web_app.src.utils.sorting import sort_machinery


# ReportScheme из ORM-записки; техника сортируется по типу и ходу выезда (п. 2.7)
def build_report_scheme(report: Report) -> ReportScheme:
    machinery = sort_machinery([MachineryScheme(**m) for m in report.data])

    return ReportScheme(
        id=report.id,
        machinery=machinery,
        section=report.section.title,
        section_id=report.section_id,
        date=report.date,
        total_personnel=report.total_personnel,
        personnel=report.personnel,
        current_personnel=report.current_personnel,
        leadership=report.leadership,
        operational_machinery=report.operational_machinery
    )


# Создаем служебную записку
@connection
async def sql_create_report(
    section_id: int,
    leadership: str,
    total_personnel: int,
    personnel: int,
    current_personnel: int,
    operational_machinery: bool,
    session: AsyncSession,
) -> None:
    try:
        # Состав техники — по единому правилу «моя техника сегодня»; машины, ушедшие в передислокацию,
        # входят отдельной строкой (в боевом расчёте не участвуют). Состояние, причина и дата обслуживания
        # берутся строго из актуальной карточки. Повторная подача за сутки перезаписывает предыдущую (снапшот дня — один).
        machineries = await sql_get_machineries(
            section_id=section_id,
            session=session,
            include_relocated_out=True,
            no_decor=True
        )

        stmt = pg_insert(Report).values(
            data=[machinery.model_dump(mode="json", exclude={"label"}) for machinery in machineries],
            section_id=section_id,
            leadership=leadership,
            date=today_msk(),
            total_personnel=total_personnel,
            personnel=personnel,
            current_personnel=current_personnel,
            operational_machinery=operational_machinery
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "section_id"],
            set_=dict(
                data=stmt.excluded.data,
                leadership=leadership,
                total_personnel=total_personnel,
                personnel=personnel,
                current_personnel=current_personnel,
                operational_machinery=operational_machinery,
                updated_at=sa.func.now()
            )
        )

        await session.execute(stmt)
        await session.commit()

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error create report by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error create report by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем служебные записки
@connection
async def sql_get_reports(
    section_id: int,
    session: AsyncSession,
    last_seen_id: int = 0,
    reports_per_page: int = 10,
) -> List[ReportScheme]:
    try:
        reports_result = await session.execute(
            sa.select(Report)
            .where(
                Report.section_id == section_id,
                Report.id > last_seen_id
            )
            .options(
                so.joinedload(Report.section)
            )
            .order_by(Report.id.desc())
            .limit(reports_per_page)
        )
        reports = reports_result.scalars()

        return [build_report_scheme(report) for report in reports]

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get reports by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get reports by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем сегодняшние строевые записки (все или только указанных ПСЧ)
@connection
async def sql_get_all_reports(
    session: AsyncSession,
    section_ids: Optional[Sequence[int]] = None,
) -> Tuple[List[ReportScheme], List[int]]:
    try:
        stmt = (
            sa.select(Report)
            .where(Report.date == today_msk())
            .options(
                so.joinedload(Report.section)
            )
            .order_by(Report.id)
        )
        if section_ids is not None:
            stmt = stmt.where(Report.section_id.in_(list(section_ids)))

        reports_result = await session.execute(stmt)

        result = []
        submitted_section_ids = []
        for report in reports_result.scalars():
            submitted_section_ids.append(report.section_id)
            result.append(build_report_scheme(report))

        # Обозначение техники в выгрузке берётся из актуальной карточки (п. 2.6): ход выезда,
        # изменённый после подачи записки, виден в следующей выгрузке без повторной подачи
        machinery_ids = {m.id for report in result for m in report.machinery}
        if machinery_ids:
            current_result = await session.execute(
                sa.select(
                    Machinery.id, Machinery.kind, Machinery.short_title, Machinery.departure_order
                ).where(Machinery.id.in_(machinery_ids))
            )
            current = {row.id: row for row in current_result}

            refreshed = []
            for report in result:
                machinery = [
                    m.model_copy(update={
                        "kind": current[m.id].kind.value,
                        "short_title": current[m.id].short_title,
                        "departure_order": current[m.id].departure_order,
                    }) if m.id in current else m
                    for m in report.machinery
                ]
                refreshed.append(report.model_copy(update={"machinery": sort_machinery(machinery)}))
            result = refreshed

        return result, submitted_section_ids

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get all reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get all reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Признак состава техники в сегодняшней записке ПСЧ: {(id машины, направление передислокации или None)}.
# None — записка за сегодня ещё не подана.
@connection
async def sql_get_today_report_signature(
    section_id: int,
    session: AsyncSession,
) -> Optional[FrozenSet[Tuple[int, Optional[str]]]]:
    try:
        data_result = await session.execute(
            sa.select(Report.data)
            .where(
                Report.section_id == section_id,
                Report.date == today_msk()
            )
        )
        data = data_result.scalar_one_or_none()

        if data is None:
            return None

        return frozenset(
            (m["id"], (m.get("relocation") or {}).get("direction"))
            for m in data
        )

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get today report signature by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")