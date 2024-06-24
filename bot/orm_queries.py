from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from .models import Trainer, Training, Attendance, Price, TrainingSchedule


async def orm_get_trainer_by_phone(session: AsyncSession, phone_number: str):
    query = select(Trainer).where(Trainer.phone_number == phone_number)
    result = await session.execute(query)
    return result.scalars().first()


async def orm_get_trainer_by_tg_id(session: AsyncSession, tg_id: str):
    query = select(Trainer).where(Trainer.trainertg_id == tg_id)
    result = await session.execute(query)
    return result.scalars().first()


async def orm_update_trainer_tg_id(session: AsyncSession, phone_number: str, tg_id: str):
    query = update(Trainer).where(Trainer.phone_number == phone_number).values(trainertg_id=tg_id)
    await session.execute(query)
    await session.commit()


async def orm_get_yesterdays_trainings(session: AsyncSession, trainer_id: int, yesterday_date):
    yesterday_weekday = yesterday_date.strftime('%a').lower()
    query = select(TrainingSchedule).join(Training).where(
        Training.trainer_id == trainer_id,
        TrainingSchedule.day_of_week == yesterday_weekday
    ).options(joinedload(TrainingSchedule.training)).order_by(TrainingSchedule.start_time)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_todays_trainings(session: AsyncSession, trainer_id: int, today_date):
    today_weekday = today_date.strftime('%a').lower()
    query = select(TrainingSchedule).join(Training).where(
        Training.trainer_id == trainer_id,
        TrainingSchedule.day_of_week == today_weekday
    ).options(joinedload(TrainingSchedule.training)).order_by(TrainingSchedule.start_time)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_add_attendance(session: AsyncSession, data: dict):
    obj = Attendance(
        training_id=data['training_id'],
        attend_count=data['attend_count'],
        recording_day=data['recording_day'],
        recording_date=data['recording_date'],
        created_date=data['created_date'],
        update_date=data['update_date']
    )
    session.add(obj)
    await session.commit()


async def orm_get_trainer_salary_for_month(session: AsyncSession, trainer_id: int, start_date, end_date):
    query = select(
        Attendance.attend_count,
        Price.price_to,
        Price.quantity_to,
        Price.price_from,
        Price.quantity_from
    ).select_from(Attendance).join(Attendance.training).join(Training.prices).where(
        Training.trainer_id == trainer_id,
        Attendance.recording_date >= start_date,
        Attendance.recording_date <= end_date
    )
    result = await session.execute(query)
    attendances = result.fetchall()

    salary = 0
    for attendance in attendances:
        if attendance.attend_count <= attendance.quantity_to:
            salary += attendance.attend_count * attendance.price_to
        else:
            salary += attendance.attend_count * attendance.price_from

    return salary
