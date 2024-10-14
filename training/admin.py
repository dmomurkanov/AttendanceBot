from django.contrib import admin
from django.http import HttpResponse
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from django.db.models import Sum, F, Case, When, IntegerField
from .models import Trainer, Training, Attendance, Price, TrainingSchedule, DAYS_OF_WEEK
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)


def download_salary_report(modeladmin, request, queryset):
    now = datetime.now()
    start_of_month = now.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    attendances = Attendance.objects.filter(
        recording_date__range=(start_of_month, end_of_month)
    ).select_related(
        'training',
        'training__trainer'
    ).prefetch_related(
        'training__price_set'
    )

    data = []
    total_by_trainer = {}

    for attendance in attendances:
        training = attendance.training
        trainer = training.trainer
        price = Price.objects.filter(training=training).first()

        if not price:
            continue

        # Новая формула расчета
        if attendance.attend_count <= price.quantity_to:
            payment = attendance.attend_count * price.price_to
            per_class_price = price.price_to  # Цена за занятие
        else:
            payment = attendance.attend_count * price.price_from
            per_class_price = price.price_from  # Цена за занятие

        if trainer.id not in total_by_trainer:
            total_by_trainer[trainer.id] = {
                'name': trainer.full_name,
                'total': 0,
                'classes': 0
            }
        total_by_trainer[trainer.id]['total'] += payment
        total_by_trainer[trainer.id]['classes'] += 1

        training_schedule = TrainingSchedule.objects.filter(training=attendance.training).first()
        combined_datetime = attendance.recording_datetime(training_schedule)

        data.append({
            'Тренер': trainer.full_name,
            'Занятие': training.name,
            'Дата и время': combined_datetime,
            'День недели': dict(DAYS_OF_WEEK)[attendance.recording_day],
            'Количество участников': attendance.attend_count,
            'Цена': per_class_price,
            'Сумма за занятие': payment
        })

    for trainer_id, trainer_data in total_by_trainer.items():
        data.append({
            'Тренер': f"ИТОГО {trainer_data['name']}",
            'Занятие': f"Всего занятий: {trainer_data['classes']}",
            'Дата и время': None,
            'День недели': None,
            'Количество участников': None,
            'Цена': None,
            'Сумма за занятие': trainer_data['total']
        })

    df = pd.DataFrame(data)

    summary_data = [
        {
            'Тренер': trainer_data['name'],
            'Количество занятий': trainer_data['classes'],
            'Общая сумма': trainer_data['total']
        }
        for trainer_data in total_by_trainer.values()
    ]

    total_classes = sum(trainer_data['classes'] for trainer_data in total_by_trainer.values())
    total_salary = sum(trainer_data['total'] for trainer_data in total_by_trainer.values())
    summary_data.append({
        'Тренер': 'ОБЩИЙ ИТОГ',
        'Количество занятий': total_classes,
        'Общая сумма': total_salary
    })

    summary_df = pd.DataFrame(summary_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Детализация', index=False)
        summary_df.to_excel(writer, sheet_name='Итоги', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Детализация']
        summary_worksheet = writer.sheets['Итоги']

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#C0C0C0'
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E0E0E0'
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        for col_num, value in enumerate(summary_df.columns.values):
            summary_worksheet.write(0, col_num, value, header_format)

        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).apply(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_len)

        for i, col in enumerate(summary_df.columns):
            column_len = max(summary_df[col].astype(str).apply(len).max(), len(col) + 2)
            summary_worksheet.set_column(i, i, column_len)

        for row_num, row in enumerate(df.values):
            if str(row[0]).startswith('ИТОГО'):
                for col_num in range(len(row)):
                    value = row[col_num]
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        value = 0
                    worksheet.write(row_num + 1, col_num, value, total_format)

        last_row = len(summary_data)
        for col_num in range(len(summary_df.columns)):
            summary_worksheet.write(last_row, col_num, summary_df.iloc[-1][col_num], total_format)

    output.seek(0)
    filename = f'trainer_salary_report_{now.strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

download_salary_report.short_description = "Скачать отчет по зарплате"


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
    list_filter = (
            ("start_date", DateRangeFilterBuilder()),
            (
                "start_date",
                DateTimeRangeFilterBuilder(
                    title="Custom title",
                    default_start=datetime(2020, 1, 1),
                    default_end=datetime(2030, 1, 1),
                ),
            ),
#             ("num_value", NumericRangeFilterBuilder()),
            ("start_date", DateRangeQuickSelectListFilterBuilder()),  # Range + QuickSelect Filter
        )
    ordering = ('start_date',)
    inlines = [TrainingScheduleInline, PriceInline]
    actions = [download_salary_report]



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('training', 'attend_count', 'recording_day', 'recording_date')
    search_fields = ('training__name', 'recording_day')
    list_filter = ('recording_date', 'recording_day')
    ordering = ('recording_date',)
