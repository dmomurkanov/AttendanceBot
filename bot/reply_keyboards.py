from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

cancel_btn = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отмена')
        ]
    ],
    resize_keyboard=True
)

request_contact_btn = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отправить номер телефона', request_contact=True)
        ]
    ],
    resize_keyboard=True,
)

options_btn = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Занятия на сегодня'),
            KeyboardButton(text='Вчерашние занятия'),
        ],
        [
            KeyboardButton(text='Зарплата за месяц'),
        ]
    ],
    resize_keyboard=True,
)
