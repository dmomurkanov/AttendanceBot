from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

CANCEL = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отмена')
        ]
    ],
    resize_keyboard=True
)

REPLY_REQUEST_CONTACT = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отправить номер телефона', request_contact=True)
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

REPLY_OPTIONS = ReplyKeyboardMarkup(
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
