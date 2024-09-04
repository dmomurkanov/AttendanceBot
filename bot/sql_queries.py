import aiosqlite


async def get_trainer_by_phone(conn: aiosqlite.Connection, phone_number: str):
    async with conn.execute('SELECT * FROM training_trainer WHERE phone_number = ?', (phone_number,)) as cursor:
        return await cursor.fetchone()


async def get_trainer_by_tg_id(conn: aiosqlite.Connection, tg_id: str):
    async with conn.execute('SELECT * FROM training_trainer WHERE tg_id = ?', (tg_id,)) as cursor:
        return await cursor.fetchone()


async def update_trainer_tg_id(conn: aiosqlite.Connection, phone_number: str, tg_id: str):
    await conn.execute('UPDATE training_trainer SET tg_id = ? WHERE phone_number = ?', (tg_id, phone_number))
    await conn.commit()


async def get_yesterday_trainings(conn: aiosqlite.Connection, trainer_id: int, yesterday_date):
    yesterday_weekday = yesterday_date.strftime('%a').lower()
    async with conn.execute(
            '''
        SELECT ts.* FROM training_trainingschedule ts
        JOIN training_training t ON ts.training_id = t.id
        WHERE t.trainer_id = ? AND ts.day_of_week = ?
        ORDER BY ts.start_time
        ''',
            (trainer_id, yesterday_weekday)
    ) as cursor:
        return await cursor.fetchall()


async def get_today_trainings(conn: aiosqlite.Connection, trainer_id: int, today_date):
    today_weekday = today_date.strftime('%a').lower()
    async with conn.execute(
            '''
        SELECT ts.* FROM training_trainingschedule ts
        JOIN training_training t ON ts.training_id = t.id
        WHERE t.trainer_id = ? AND ts.day_of_week = ?
        ORDER BY ts.start_time
        ''',
            (trainer_id, today_weekday)
    ) as cursor:
        return await cursor.fetchall()


async def add_or_update_attendance(conn: aiosqlite.Connection, data: dict):
    async with conn.execute(
            '''
        SELECT * FROM training_attendance 
        WHERE training_id = ? AND recording_date = ?
        ''',
            (data['training_id'], data['recording_date'])
    ) as cursor:
        attendance = await cursor.fetchone()

    if attendance:
        await conn.execute(
            '''
            UPDATE training_attendance 
            SET attend_count = ?, recording_day = ?, update_date = ? 
            WHERE training_id = ? AND recording_date = ?
            ''',
            (data['attend_count'], data['recording_day'], data['update_date'], data['training_id'],
             data['recording_date'])
        )
    else:
        await conn.execute(
            '''
            INSERT INTO training_attendance (training_id, attend_count, recording_day, recording_date, created_date, update_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (data['training_id'], data['attend_count'], data['recording_day'], data['recording_date'],
             data['created_date'], data['update_date'])
        )

    await conn.commit()


async def get_trainer_salary_for_month(conn: aiosqlite.Connection, trainer_id: int, start_date, end_date):
    async with conn.execute(
            '''
        SELECT a.attend_count, p.price_to, p.quantity_to, p.price_from, p.quantity_from 
        FROM training_attendance a 
        JOIN training_training t ON a.training_id = t.id 
        JOIN training_price p ON t.id = p.training_id 
        WHERE t.trainer_id = ? AND a.recording_date BETWEEN ? AND ?
        ''',
            (trainer_id, start_date, end_date)
    ) as cursor:
        attendances = await cursor.fetchall()

    salary = 0
    for attendance in attendances:
        if attendance['attend_count'] <= attendance['quantity_to']:
            salary += attendance['attend_count'] * attendance['price_to']
        else:
            salary += attendance['attend_count'] * attendance['price_from']

    return salary


async def get_training_id_by_schedule_id(conn: aiosqlite.Connection, schedule_id: int):
    async with conn.execute(
            'SELECT training_id FROM training_trainingschedule WHERE id = ?',
            (schedule_id,)
    ) as cursor:
        return await cursor.fetchone()


async def get_training_by_id(conn: aiosqlite.Connection, training_id: int):
    async with conn.execute(
        'SELECT name FROM training_training WHERE id = ?',
        (training_id,)
    ) as cursor:
        return await cursor.fetchone()
