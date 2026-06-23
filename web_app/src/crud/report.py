# Внешние зависимости
from typing import List, Tuple
from datetime import date
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import Report
from web_app.src.crud import sql_get_machineries
from web_app.src.schemas import ReportScheme, MachineryScheme


# Создаем служебную записку
@connection
async def sql_create_report(
    section_id: int,
    leadership: str,
    total_personnel: int,
    personnel: int,
    current_personnel: int,
    session: AsyncSession,
) -> None:
    try:
        machineries = await sql_get_machineries(
            section_id=section_id,
            session=session,
            no_decor=True
        )
        await session.rollback()

        stmt = pg_insert(Report).values(
            data=[machinery.model_dump(mode="json") for machinery in machineries],
            section_id=section_id,
            leadership=leadership,
            date=date.today(),
            total_personnel=total_personnel,
            personnel=personnel,
            current_personnel=current_personnel,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "section_id"],
            set_=dict(
                data=stmt.excluded.data,
                leadership=leadership,
                total_personnel=total_personnel,
                personnel=personnel,
                current_personnel=current_personnel,
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
            .order_by(Report.id)
            .limit(reports_per_page)
        )
        reports = reports_result.scalars()

        result = []
        for report in reports:
            result.append(ReportScheme(
                id=report.id,
                machinery=[MachineryScheme(**m) for m in report.data],
                section=report.section.title,
                date=report.date,
                total_personnel=report.total_personnel,
                personnel=report.personnel,
                current_personnel=report.current_personnel,
                leadership=report.leadership
            ))

        return result

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get reports by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get reports by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем служебные записки
@connection
async def sql_get_all_reports(
    session: AsyncSession
) -> Tuple[List[ReportScheme], List[int]]:
    try:
        reports_result = await session.execute(
            sa.select(Report)
            .where(
                Report.date == date.today()
            )
            .options(
                so.joinedload(Report.section)
            )
            .order_by(Report.id)
        )
        reports = reports_result.scalars()

        result = []
        section_ids = []
        for report in reports:
            section_ids.append(report.section.id)

            result.append(ReportScheme(
                id=report.id,
                machinery=[MachineryScheme(**m) for m in report.data],
                section=report.section.title,
                date=report.date,
                total_personnel=report.total_personnel,
                personnel=report.personnel,
                current_personnel=report.current_personnel,
                leadership=report.leadership
            ))

        return result, section_ids

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get all reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get all reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")