from django.db import models
import re
from django.utils.formats import date_format
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Trainer(models.Model):
    """
    Модель для представления тренера.
    """
    PHONE_REGEX = re.compile(
        r'996(880\d{2}|755\d{2}|22[0-9]\d{2}|99[9]\d{2}|77([0-37-9]\d{2}|5(58|9[7-9]))|(5[0157]|70)\d{3}|54(3\d{2}|59[5-6])|56(550|6(9\d|47|69|8[7-9]))|20[0-35]\d{2})\d{4}')

    first_name = models.CharField(verbose_name='Имя', max_length=20)
    last_name = models.CharField(verbose_name='Фамилия', max_length=20)
    phone_number = models.CharField(
        verbose_name='Номер телефона',
        help_text='В международном формате без знака +',
        unique=True,
        max_length=12,
        validators=[
            RegexValidator(
                PHONE_REGEX,
                'Номер телефона должен соответствовать формату Кыргызской Республики без знака +'
            )
        ]
    )
    trainertg_id = models.CharField(
        max_length=16, unique=True, null=True, blank=True,
        verbose_name='Telegram ID тренера', help_text='Заполнять не нужно'
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренера'


class Training(models.Model):
    """
    Модель для представления тренировок.
    """
    name = models.CharField(verbose_name='Занятие', max_length=64)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тренер')
    start_date = models.DateField(verbose_name='Дата начала занятий')
    end_date = models.DateField(verbose_name='Дата конца занятий')

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("Дата окончания не может быть раньше даты начала.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'


class TrainingSchedule(models.Model):
    """
    Модель для представления расписания тренировок.
    """
    DAYS_OF_WEEK = [
        ('mon', 'Понедельник'),
        ('tue', 'Вторник'),
        ('wed', 'Среда'),
        ('thu', 'Четверг'),
        ('fri', 'Пятница'),
        ('sat', 'Суббота'),
        ('sun', 'Воскресенье'),
    ]

    training = models.ForeignKey(Training, related_name='schedules', on_delete=models.CASCADE, verbose_name='Занятие')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Время начала занятия')
    end_time = models.TimeField(verbose_name='Время конца занятия')

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    class Meta:
        verbose_name = 'Расписание занятия'
        verbose_name_plural = 'Расписания занятий'
        unique_together = ('training', 'day_of_week', 'start_time')


class Attendance(models.Model):
    """
    Модель для учета посещаемости тренировок.
    """
    DAYS_OF_WEEK = TrainingSchedule.DAYS_OF_WEEK

    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name='Занятие')
    attend_count = models.PositiveSmallIntegerField(verbose_name='Количество участников', default=0)
    recording_day = models.CharField(
        max_length=3, verbose_name='День недели', choices=DAYS_OF_WEEK
    )
    recording_date = models.DateField(verbose_name='Дата записи')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    update_date = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def save(self, *args, **kwargs):
        if not self.recording_day:
            self.recording_day = date_format(self.recording_date, 'l').lower()[:3]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'На занятие {self.training.name} пришло {self.attend_count} чел. Дата {self.recording_date}'

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'


class Price(models.Model):
    """
    Модель для представления цен на занятия.
    """
    training = models.ForeignKey(Training, on_delete=models.CASCADE, verbose_name='Занятие')
    quantity_to = models.PositiveSmallIntegerField(verbose_name='Количество участников до включительно')
    price_to = models.PositiveIntegerField(verbose_name='Цена до')
    quantity_from = models.PositiveSmallIntegerField(verbose_name='Количество участников от включительно')
    price_from = models.PositiveIntegerField(verbose_name='Цена от')

    def __str__(self):
        return f'Цена до {self.quantity_to} чел. включительно: {self.price_to}, цена от {self.quantity_from} чел. включительно: {self.price_from}'

    class Meta:
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
