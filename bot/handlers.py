from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime
from django.utils import timezone

import os
import django

from .models import DaysOfWeek
from .orm_queries import (
    orm_get_trainer_by_phone,
    orm_get_trainer_by_tg_id,
    orm_update_trainer_tg_id,
    orm_get_yesterdays_trainings,
    orm_get_todays_trainings,
    orm_get_trainer_salary_for_month, orm_get_training_id_by_schedule_id, orm_add_or_update_attendance
)
from .reply_keyboards import REPLY_REQUEST_CONTACT, REPLY_OPTIONS, CANCEL

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trainingmanager.settings')
django.setup()

router = Router()


def register_handlers(dp):
    dp.include_router(router)


class AttendanceStates(StatesGroup):
    training_id = State()
    attendance_count = State()
    date = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        pass
    await state.clear()
    await message.answer(
        "Пожалуйста, отправьте свой номер телефона",
        reply_markup=REPLY_REQUEST_CONTACT
    )


@router.message(F.contact)
async def handle_contact(message: Message, session: AsyncSession):
    trainer_phone = message.contact.phone_number
    print(f"Received phone number: {trainer_phone}")
    if trainer_phone[0] == "+":
        trainer_phone = trainer_phone[1:]

    trainer = await orm_get_trainer_by_phone(session, trainer_phone)
    if trainer:
        if trainer.trainertg_id:
            await message.answer("Ваш номер телефона уже зарегистрирован в системе", reply_markup=REPLY_OPTIONS)
        else:
            await orm_update_trainer_tg_id(session, trainer_phone, str(message.from_user.id))
            await message.answer("Ваш номер телефона сохранен", reply_markup=REPLY_OPTIONS)
    else:
        await message.answer("Ваш номер телефона не зарегистрирован в системе")


@router.message(StateFilter('*'), F.text.casefold() == "вчерашние занятия")
async def send_yesterdays_trainings(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        pass
    await state.clear()

    trainer = await orm_get_trainer_by_tg_id(session, str(message.from_user.id))
    if not trainer:
        await message.answer("Ваш номер телефона не найден. Используйте команду /start")
        return

    yesterday = timezone.now().date() - timedelta(days=1)
    print(f"Trainer ID: {trainer.id}, Yesterday: {yesterday}, Weekday: {yesterday.strftime('%A')}")
    schedules = await orm_get_yesterdays_trainings(session, trainer.id, yesterday)
    print(f"Schedules found: {schedules}")

    if not schedules:
        await message.answer("Вчера у вас не было занятий")
    else:
        inline_keyboard = InlineKeyboardBuilder()
        for schedule in schedules:
            button_text = f"{schedule.training.name} с {schedule.start_time.strftime('%H:%M')} до {schedule.end_time.strftime('%H:%M')}"
            inline_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"yesattendance_{schedule.id}"))
        inline_keyboard.adjust(1)
        await message.answer("Ваши вчерашние занятия", reply_markup=inline_keyboard.as_markup())


@router.message(StateFilter('*'), F.text.casefold() == "занятия на сегодня")
async def send_todays_trainings(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        pass
    await state.clear()

    trainer = await orm_get_trainer_by_tg_id(session, str(message.from_user.id))
    if not trainer:
        await message.answer("Ваш номер телефона не найден. Используйте команду /start")
        return

    today = timezone.now().date()
    print(f"Trainer ID: {trainer.id}, Today: {today}, Weekday: {today.strftime('%A')}")
    schedules = await orm_get_todays_trainings(session, trainer.id, today)
    print(f"Schedules found: {schedules}")

    if not schedules:
        await message.answer("На сегодня у вас нет занятий")
    else:
        inline_keyboard = InlineKeyboardBuilder()
        for schedule in schedules:
            button_text = f"{schedule.training.name} с {schedule.start_time.strftime('%H:%M')} до {schedule.end_time.strftime('%H:%M')}"
            inline_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"todattendance_{schedule.id}"))
        inline_keyboard.adjust(1)
        await message.answer("Ваши занятия на сегодня", reply_markup=inline_keyboard.as_markup())


@router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        pass
    await state.clear()
    await message.answer("Действия отменены", reply_markup=REPLY_OPTIONS)


@router.callback_query(F.data.startswith("yesattendance_"))
async def yesterdays_t(callback: CallbackQuery, state: FSMContext):
    schedule_id = callback.data.split('_')[1]
    yesterday_date = (timezone.now() - timedelta(days=1)).date().strftime('%Y-%m-%d')
    await callback.message.answer('Введите количество пришедших на вчерашнее занятие', reply_markup=CANCEL)
    await state.set_state(AttendanceStates.attendance_count)
    await state.update_data(training_id=schedule_id, date=yesterday_date)
    await callback.answer()


@router.callback_query(F.data.startswith('todattendance_'))
async def attendance_recording(callback: CallbackQuery, state: FSMContext):
    schedule_id = callback.data.split('_')[1]
    await callback.message.answer('Введите количество пришедших на занятие', reply_markup=CANCEL)
    await state.set_state(AttendanceStates.attendance_count)
    await state.update_data(training_id=schedule_id)
    await callback.answer()


@router.message(AttendanceStates.attendance_count)
async def handle_attendance_count(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    data = await state.get_data()
    schedule_id = data['training_id']
    participants = int(message.text)
    date_str = data.get('date', timezone.now().date().strftime('%Y-%m-%d'))

    # Преобразование строки даты в объект datetime.date
    date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Получение training_id с использованием schedule_id
    training_id = await orm_get_training_id_by_schedule_id(session, schedule_id)
    if not training_id:
        await message.answer("Ошибка: занятие не найдено.")
        return

    weekday_map = {
        'mon': DaysOfWeek.mon,
        'tue': DaysOfWeek.tue,
        'wed': DaysOfWeek.wed,
        'thu': DaysOfWeek.thu,
        'fri': DaysOfWeek.fri,
        'sat': DaysOfWeek.sat,
        'sun': DaysOfWeek.sun
    }
    recording_day = weekday_map[date.strftime("%a").lower()]
    attendance_data = {
        'training_id': training_id,
        'attend_count': participants,
        'recording_day': recording_day,
        'recording_date': date,
        'created_date': timezone.now(),
        'update_date': timezone.now()
    }
    attendance = await orm_add_or_update_attendance(session, attendance_data)
    await message.answer(f'Количество участников успешно записано: {attendance}', reply_markup=REPLY_OPTIONS)
    await state.clear()


@router.message(StateFilter('*'), F.text.casefold() == "зарплата за месяц")
async def send_monthly_salary(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        pass
    await state.clear()

    trainer = await orm_get_trainer_by_tg_id(session, str(message.from_user.id))
    if not trainer:
        await message.answer("Ваш номер телефона не найден. Используйте команду /start")
        return

    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=1) + timedelta(days=32)
    end_of_month = end_of_month.replace(day=1) - timedelta(days=1)

    salary = await orm_get_trainer_salary_for_month(session, trainer.id, start_of_month, end_of_month)
    if salary is None:
        salary = 0

    await message.answer(f"Ваша зарплата за текущий месяц составляет: {salary} сом")


@router.message()
async def everything_else(message: Message):
    await message.answer("Я тебя не понимаю")
