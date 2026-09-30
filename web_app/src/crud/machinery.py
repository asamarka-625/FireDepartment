# Внешние зависимости
from typing import List, Optional, Sequence, Dict, Literal
from datetime import date
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, IntegrityError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import (Machinery, STATUS_MAINTENANCE_MAP, StatusMaintenance, RELOCATABLE_STATUSES,
                                REVERSE_STATUS_MAINTENANCE_MAP, Maintenance, Section, Relocation)
from web_app.src.schemas import UpdateMachineryRequest, MachineryScheme, RelocationInfoScheme
from web_app.src.utils.machinery_rules import today_msk, is_autotanker, validate_departure_order
from web_app.src.utils.sorting import sort_machinery


# Сообщение при попытке передислоцировать / оставить в передислокации технику в неподходящем состоянии
RELOCATION_STATUS_ERROR = (
    "Передислокация допустима только для техники в состоянии «Включено» или «Резерв» "
    "(включая «Резерв (ЛСО)» и «Резерв (ЛСБ)»)"
)


# Активные на дату передислокации для набора машин: {machinery_id: Relocation}
async def load_active_relocations(
    session: AsyncSession,
    machinery_ids: Sequence[int],
    on_date: date
) -> Dict[int, Relocation]:
    if not machinery_ids:
        return {}

    result = await session.execute(
        sa.select(Relocation)
        .where(
            Relocation.machinery_id.in_(machinery_ids),
            Relocation.active_clause(on_date)
        )
        .options(
            so.joinedload(Relocation.from_section),
            so.joinedload(Relocation.to_section)
        )
    )

    return {r.machinery_id: r for r in result.scalars()}


# Схема машины из ORM-объекта. section_id — ПСЧ, «глазами» которой смотрим на машину (для direction).
def build_machinery_scheme(
    machinery: Machinery,
    relocation: Optional[Relocation] = None,
    viewer_section_id: Optional[int] = None
) -> MachineryScheme:
    relocation_info = None

    if relocation is not None:
        # Если смотрим со стороны принимающей ПСЧ — машина принята («in»), иначе передана («out»)
        if viewer_section_id is not None and relocation.to_section_id == viewer_section_id:
            direction: Literal["in", "out"] = "in"
            partner = relocation.from_section
        else:
            direction = "out"
            partner = relocation.to_section

        relocation_info = RelocationInfoScheme(
            direction=direction,
            partner_id=partner.id,
            partner=partner.title,
            date_from=relocation.date_from,
            date_to=relocation.date_to
        )

    maintenance = machinery.maintenance

    return MachineryScheme(
        id=machinery.id,
        title=machinery.title,
        model=machinery.model,
        number=machinery.number,
        status=STATUS_MAINTENANCE_MAP[machinery.status.value],
        supervisor=machinery.supervisor,
        current_personnel=machinery.current_personnel,
        gdzs=machinery.gdzs,
        maintenance=(
            {"note": maintenance.note, "date": maintenance.date} if maintenance else None
        ),
        kind=machinery.kind.value,
        short_title=machinery.short_title,
        departure_order=machinery.departure_order,
        section_id=machinery.section_id,
        section=machinery.section.title if "section" in machinery.__dict__ else None,
        relocation=relocation_info
    )


# Получаем список машин ПСЧ на дату — единая точка правила «моя техника сегодня» (п. 3.2 ТЗ):
#  * вся штатная техника ПСЧ, кроме машин с активной передислокацией в другую ПСЧ;
#  * плюс машины, переданные в эту ПСЧ (relocation.direction == "in").
# include_relocated_out=True дополнительно возвращает штатные машины, ушедшие в другую ПСЧ
# (relocation.direction == "out") — они нужны для строки в записке и для отмены передислокации,
# но в «боевом расчёте» не участвуют.
@connection
async def sql_get_machineries(
    section_id: int,
    session: AsyncSession,
    on_date: Optional[date] = None,
    include_relocated_out: bool = False,
) -> List[MachineryScheme]:
    try:
        on_date = on_date or today_msk()

        condition = Machinery.on_duty_clause(section_id, on_date)
        if include_relocated_out:
            condition = sa.or_(condition, Machinery.section_id == section_id)

        machineries_result = await session.execute(
            sa.select(Machinery)
            .where(condition)
            .options(
                so.joinedload(Machinery.maintenance),
                so.joinedload(Machinery.section)
            )
        )
        machineries = list(machineries_result.unique().scalars())

        relocations = await load_active_relocations(session, [m.id for m in machineries], on_date)

        result = [
            build_machinery_scheme(m, relocations.get(m.id), viewer_section_id=section_id)
            for m in machineries
        ]

        return sort_machinery(result)

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get machineries by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get machineries by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Права пользователя на машину на дату: "owner" — машина штатно за одной из его ПСЧ,
# "receiver" — принята по передислокации, None — нет доступа.
# section_ids=None — доступ ко всему (администратор).
@connection
async def sql_get_machinery_access(
    machinery_id: int,
    section_ids: Optional[Sequence[int]],
    session: AsyncSession,
    on_date: Optional[date] = None,
) -> Optional[Literal["owner", "receiver"]]:
    try:
        on_date = on_date or today_msk()

        result = await session.execute(
            sa.select(Machinery.section_id, Machinery.effective_section_id(on_date))
            .where(Machinery.id == machinery_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        owner_section_id, effective_section_id = row

        if section_ids is None or owner_section_id in section_ids:
            return "owner"

        if effective_section_id in section_ids:
            return "receiver"

        return None

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get machinery access by machinery_id: {machinery_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


# Обновляем информации о машине.
# crew_only=True — принимающая ПСЧ: меняет только сегодняшний расчёт (старший, личный состав, ГДЗС),
# состояние и обслуживание остаются за штатной ПСЧ.
@connection
async def sql_update_machinery(
    update: UpdateMachineryRequest,
    session: AsyncSession,
    crew_only: bool = False,
) -> None:
    try:
        machinery_result = await session.execute(
            sa.select(Machinery)
            .where(Machinery.id == update.id)
            .with_for_update()
        )
        machinery = machinery_result.scalar_one()

        values = dict(
            supervisor=update.supervisor,
            current_personnel=update.current_personnel,
            gdzs=update.gdzs
        )

        if not crew_only:
            new_status = REVERSE_STATUS_MAINTENANCE_MAP.get(update.status, StatusMaintenance.OFF)

            # Пока машина в передислокации, переводить её в «ТО/Ремонт/ВП/Выключена» нельзя (п. 3.4)
            if new_status not in RELOCATABLE_STATUSES:
                active = await load_active_relocations(session, [machinery.id], today_msk())
                if machinery.id in active:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Техника передислоцирована. Сначала отмените передислокацию. "
                               + RELOCATION_STATUS_ERROR
                    )

            values["status"] = new_status

            # Ход выезда (только у АЦ, уникален в пределах ПСЧ) — п. 2.5
            if "departure_order" in update.model_fields_set and is_autotanker(machinery.short_title):
                taken_result = await session.execute(
                    sa.select(Machinery.departure_order)
                    .where(
                        Machinery.section_id == machinery.section_id,
                        Machinery.id != machinery.id,
                        Machinery.departure_order.isnot(None)
                    )
                )
                error = validate_departure_order(
                    machinery.short_title, update.departure_order, set(taken_result.scalars())
                )
                if error:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)

                values["departure_order"] = update.departure_order

        await session.execute(
            sa.update(Machinery)
            .where(Machinery.id == update.id)
            .values(**values)
        )

        if not crew_only:
            if update.maintenance:
                maintenance_id_result = await session.execute(
                    sa.update(Maintenance)
                    .where(Maintenance.machinery_id == machinery.id)
                    .values(
                        note=update.maintenance.note,
                        date=update.maintenance.date
                    )
                    .returning(Maintenance.id)
                )

                if maintenance_id_result.scalar_one_or_none() is None:
                    session.add(Maintenance(
                        machinery_id=machinery.id,
                        note=update.maintenance.note,
                        date=update.maintenance.date
                    ))

            else:
                # Признак «Обслуживание» снят — причина и дата удаляются из карточки,
                # чтобы они не попадали в новую строевую записку (п. 1.2)
                await session.execute(
                    sa.delete(Maintenance)
                    .where(Maintenance.machinery_id == machinery.id)
                )

        await session.commit()

    except HTTPException:
        raise

    except IntegrityError:
        # гонка: тот же ход выезда занят параллельным запросом
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой ход выезда уже занят другой автоцистерной этой ПСЧ"
        )

    except NoResultFound:
        cfg.logger.info(f"Machinery not found by machinery_id: {update.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machinery not found")

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error update machinery by machinery_id: {update.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error update machinery by machinery_id: {update.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем всю технику с обслуживанием и подразделением (для листа «Техника»).
# Машина остаётся в блоке штатной ПСЧ; передислокация выводится пометкой в статусе (п. 3.6).
# section_ids — ограничить набором ПСЧ (подавшие строевую записку / своя ПСЧ).
@connection
async def sql_get_all_machineries(
    session: AsyncSession,
    section_ids: Optional[Sequence[int]] = None,
    on_date: Optional[date] = None,
) -> List[dict]:
    try:
        on_date = on_date or today_msk()

        stmt = (
            sa.select(Machinery)
            .join(Machinery.section)
            .options(
                so.joinedload(Machinery.section),
                so.joinedload(Machinery.maintenance)
            )
            .order_by(Section.title, Machinery.id)
        )
        if section_ids is not None:
            stmt = stmt.where(Machinery.section_id.in_(list(section_ids)))

        result = await session.execute(stmt)
        machineries_orm = list(result.unique().scalars())

        relocations = await load_active_relocations(session, [m.id for m in machineries_orm], on_date)

        machineries = []
        for m in machineries_orm:
            relocation = relocations.get(m.id)

            machineries.append({
                "section": m.section.title,
                "title": m.title,
                "model": m.model,
                "number": m.number,
                "status": STATUS_MAINTENANCE_MAP[m.status.value],
                "kind": m.kind.value,
                "short_title": m.short_title,
                "departure_order": m.departure_order,
                "supervisor": m.supervisor,
                "current_personnel": m.current_personnel,
                "gdzs": m.gdzs,
                "maintenance_note": m.maintenance.note if m.maintenance else "",
                "maintenance_date": m.maintenance.date if m.maintenance else None,
                "relocation_to": relocation.to_section.title if relocation else None,
                "relocation_from_date": relocation.date_from if relocation else None,
            })

        return machineries

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get all machineries: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get all machineries: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")