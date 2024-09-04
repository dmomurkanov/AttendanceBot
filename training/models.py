from django.core.exceptions import ValidationError
from django.db import models


DAYS_OF_WEEK = [
    ('mon', 'Понедельник'),
    ('tue', 'Вторник'),
    ('wed', 'Среда'),
    ('thu', 'Четверг'),
    ('fri', 'Пятница'),
    ('sat', 'Суббота'),
    ('sun', 'Воскресенье'),
]


class Trainer(models.Model):
    first_name = models.CharField(verbose_name='Имя', max_length=20)
    last_name = models.CharField(verbose_name='Фамилия', max_length=20)
    phone_number = models.CharField(
        verbose_name='Номер телефона',
        help_text='В международном формате без знака +',
        unique=True,
        max_length=12,
    )
    tg_id = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Telegram ID тренера',
        help_text='Заполнять не нужно'
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренера'


class Training(models.Model):
    name = models.CharField(verbose_name='Занятие', max_length=64)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тренер')
    start_date = models.DateField(verbose_name='Дата начала занятий')
    end_date = models.DateField(verbose_name='Дата конца занятий')

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Дата начала должна быть меньше или равна дате окончания.")

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'


class TrainingSchedule(models.Model):
    training = models.ForeignKey(Training, related_name='schedules', on_delete=models.CASCADE, verbose_name='Занятие')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Время начала занятия')
    end_time = models.TimeField(verbose_name='Время конца занятия')

    def __str__(self):
        return f"{self.training} {self.start_time}-{self.end_time}"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Время начала занятия должно быть меньше времени окончания.")

    class Meta:
        verbose_name = 'Расписание занятия'
        verbose_name_plural = 'Расписания занятий'
        unique_together = ('training', 'day_of_week', 'start_time')


class Attendance(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name='Занятие')
    attend_count = models.PositiveSmallIntegerField(verbose_name='Количество участников', default=0)
    recording_day = models.CharField(
        max_length=3, verbose_name='День недели', choices=DAYS_OF_WEEK
    )
    recording_date = models.DateField(verbose_name='Дата записи')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    update_date = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'На занятие {self.training.name} пришло {self.attend_count} чел. Дата {self.recording_date}'

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'


class Price(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name='Занятие')
    quantity_to = models.PositiveSmallIntegerField(verbose_name='Количество участников до включительно')
    price_to = models.PositiveIntegerField(verbose_name='Цена до')
    quantity_from = models.PositiveSmallIntegerField(verbose_name='Количество участников от включительно')
    price_from = models.PositiveIntegerField(verbose_name='Цена от')

    def __str__(self):
        return f'{self.training.name}: До {self.quantity_to} {self.price_to}. От {self.quantity_from} {self.price_from}'

    def clean(self):
        super().clean()
        if self.quantity_to and self.quantity_from and self.quantity_to > self.quantity_from:
            raise ValidationError("Количество 'до' не может быть больше количества 'от'.")
        if self.price_to and self.price_from and self.price_to > self.price_from:
            raise ValidationError("Цена 'до' не может быть больше цены 'от'.")

    class Meta:
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
