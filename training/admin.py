from django.contrib import admin

from .models import Trainer, Training, Attendance, Price, TrainingSchedule


class PriceInline(admin.TabularInline):
    model = Price
    extra = 1
    max_num = 1
    fields = ('quantity_to', 'price_to', 'quantity_from', 'price_from')
    verbose_name = "Цена"
    verbose_name_plural = "Цены"


class TrainingScheduleInline(admin.TabularInline):
    model = TrainingSchedule
    extra = 1
    fields = ('day_of_week', 'start_time', 'end_time')
    verbose_name = "Расписание"
    verbose_name_plural = "Расписания"


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number')
    search_fields = ('first_name', 'last_name', 'phone_number')


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'start_date', 'end_date')
    search_fields = ('name', 'trainer__first_name', 'trainer__last_name')
    list_filter = ('start_date', 'end_date')
    ordering = ('start_date',)
    inlines = [TrainingScheduleInline, PriceInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('training', 'attend_count', 'recording_day', 'recording_date')
    search_fields = ('training__name', 'recording_day')
    list_filter = ('recording_date', 'recording_day')
    ordering = ('recording_date',)
