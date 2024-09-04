import os
import asyncio

import aiosqlite
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder
from datetime import datetime, timedelta

from bot.reply_keyboards import request_contact_btn, cancel_btn, options_btn
from bot.logger import configure_logging
from bot.sql_queries import (
    get_trainer_by_phone,
    get_trainer_by_tg_id,
    update_trainer_tg_id,
    get_yesterday_trainings,
    get_today_trainings,
    add_or_update_attendance,
    get_trainer_salary_for_month,
    get_training_id_by_schedule_id
)

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def connect_to_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')
    conn = await aiosqlite.connect(database=db_path)
    conn.row_factory = aiosqlite.Row
    return conn


class AttendanceStates(StatesGroup):
    training_id = State()
    attendance_count = State()
    date = State()


@dp.message(Command('start'))
async def start_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        pass

    await state.clear()
    await message.answer(
        'Пожалуйста, отправьте свой номер телефона *нажав на кнопку*',
        reply_markup=request_contact_btn,
        parse_mode=ParseMode.MARKDOWN_V2
    )


@dp.message(F.contact)
async def handle_contact(message: Message):
    conn = dp['dbconn']
    trainer_phone = message.contact.phone_number
    telegram_id = str(message.from_user.id)
    if trainer_phone[0] == "+":
        trainer_phone = trainer_phone[1:]

    trainer = await get_trainer_by_phone(conn, trainer_phone)
    if trainer:
        if trainer['tg_id']:
            await message.answer("Ваш номер телефона уже зарегистрирован в системе", reply_markup=options_btn)
        else:
            await update_trainer_tg_id(conn, trainer_phone, telegram_id)
            await message.answer("Ваш номер телефона был сохранен", reply_markup=options_btn)
    else:
        await message.answer("Ваш номер телефона не был найден в базе", reply_markup=ReplyKeyboardRemove())


@dp.message(StateFilter('*'), F.text.casefold() == "вчерашние занятия")
async def send_yesterdays_trainings(message: Message, state: FSMContext):
    await state.clear()

    conn = dp['dbconn']
    telegram_id = str(message.from_user.id)

    trainer = await get_trainer_by_tg_id(conn, telegram_id)
    if not trainer:
        await message.answer("Ваш номер телефона не найден в базе. Используйте команду /start")
        return

    yesterday = datetime.now().date() - timedelta(days=1)
    schedules = await get_yesterday_trainings(conn, trainer['id'], yesterday)

    if not schedules:
        await message.answer("Вчера у вас не было занятий")
    else:
        inline_keyboard = InlineKeyboardBuilder()
        for schedule in schedules:
            button_text = f"{schedule['training_name']} с {schedule['start_time']} до {schedule['end_time']}"
            inline_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"yesattendance_{schedule['id']}"))
        inline_keyboard.adjust(1)
        await message.answer("Ваши вчерашние занятия", reply_markup=inline_keyboard.as_markup())


@dp.message(StateFilter('*'), F.text.casefold() == "занятия на сегодня")
async def send_todays_trainings(message: Message, state: FSMContext):
    await state.clear()

    conn = dp['dbconn']
    telegram_id = str(message.from_user.id)

    trainer = await get_trainer_by_tg_id(conn, telegram_id)
    if not trainer:
        await message.answer("Ваш номер телефона не найден. Используйте команду /start")
        return

    today = datetime.now().date()
    schedules = await get_today_trainings(conn, trainer['id'], today)

    if not schedules:
        await message.answer("На сегодня у вас нет занятий")
    else:
        inline_keyboard = InlineKeyboardBuilder()
        for schedule in schedules:
            button_text = f"{schedule['training_name']} с {schedule['start_time']} до {schedule['end_time']}"
            inline_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"todattendance_{schedule['id']}"))
        inline_keyboard.adjust(1)
        await message.answer("Ваши занятия на сегодня", reply_markup=inline_keyboard.as_markup())


@dp.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действия отменены", reply_markup=options_btn)


@dp.callback_query(F.data.startswith("yesattendance_"))
async def yesterdays_t(callback: CallbackQuery, state: FSMContext):
    schedule_id = int(callback.data.split('_')[1])
    yesterday_date = (datetime.now() - timedelta(days=1)).date().strftime('%Y-%m-%d')
    await callback.message.answer('Введите количество пришедших на вчерашнее занятие', reply_markup=cancel_btn)
    await state.set_state(AttendanceStates.attendance_count)
    await state.update_data(training_id=schedule_id, date=yesterday_date)
    await callback.answer()


@dp.callback_query(F.data.startswith('todattendance_'))
async def attendance_recording(callback: CallbackQuery, state: FSMContext):
    schedule_id = int(callback.data.split('_')[1])
    await callback.message.answer('Введите количество пришедших на занятие', reply_markup=cancel_btn)
    await state.set_state(AttendanceStates.attendance_count)
    await state.update_data(training_id=schedule_id)
    await callback.answer()


@dp.message(AttendanceStates.attendance_count)
async def handle_attendance_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return

    data = await state.get_data()
    schedule_id = data['training_id']
    participants = int(message.text)
    date_str = data.get('date', datetime.now().date().strftime('%Y-%m-%d'))

    date = datetime.strptime(date_str, '%Y-%m-%d').date()

    training_id_result = await get_training_id_by_schedule_id(dp['dbconn'], schedule_id)
    if not training_id_result:
        await message.answer("Ошибка: занятие не найдено.")
        return

    training_id = training_id_result['training_id']

    weekday_map = {
        'mon': 'mon',
        'tue': 'tue',
        'wed': 'wed',
        'thu': 'thu',
        'fri': 'fri',
        'sat': 'sat',
        'sun': 'sun'
    }
    recording_day = weekday_map[date.strftime("%a").lower()]

    attendance_data = {
        'training_id': training_id,
        'attend_count': participants,
        'recording_day': recording_day,
        'recording_date': date,
        'created_date': datetime.now(),
        'update_date': datetime.now()
    }
    await add_or_update_attendance(dp['dbconn'], attendance_data)
    await message.answer(f'Количество участников успешно записано: {attendance_data["attend_count"]}',
                         reply_markup=options_btn)
    await state.clear()


@dp.message(StateFilter('*'), F.text.casefold() == "зарплата за месяц")
async def send_monthly_salary(message: Message, state: FSMContext):
    await state.clear()

    conn = dp['dbconn']
    telegram_id = str(message.from_user.id)

    trainer = await get_trainer_by_tg_id(conn, telegram_id)
    if not trainer:
        await message.answer("Ваш номер телефона не найден. Используйте команду /start")
        return

    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    end_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    salary = await get_trainer_salary_for_month(conn, trainer['id'], start_of_month, end_of_month)
    if salary is None:
        salary = 0

    await message.answer(f"Ваша зарплата за текущий месяц составляет: {salary} сом")


@dp.message()
async def everything_else(message: Message):
    await message.answer("Я тебя не понимаю")


async def main():
    configure_logging()
    dp['dbconn'] = await connect_to_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
