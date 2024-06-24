from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from openpyxl import Workbook
import urllib

from .models import Trainer, Training, Attendance, Price, TrainingSchedule
from .forms import DateRangeForm


def export_trainers_data_to_excel(request, trainer_ids=None, start_date=None, end_date=None):
    wb = Workbook()
    ws = wb.active
    ws.append(['ТРЕНЕР', 'ЗАНЯТИЕ', 'ДАТА', 'ВРЕМЯ', 'УЧАСТНИКИ', 'СУММА'])

    if start_date and end_date:
        attendances_filter = {
            'created_date__range': [start_date, end_date]
        }
    else:
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        attendances_filter = {
            'created_date__year': current_year,
            'created_date__month': current_month
        }

    if trainer_ids:
        trainers = Trainer.objects.filter(id__in=trainer_ids)
    else:
        trainers = Trainer.objects.all()

    for trainer in trainers:
        trainings = Training.objects.filter(trainer=trainer)

        for training in trainings:
            attendances = Attendance.objects.filter(training=training, **attendances_filter)

            for attendance in attendances:
                participant_count = attendance.attend_count

                price_to = Price.objects.filter(training=training, quantity_to__gte=participant_count).order_by(
                    'quantity_to').first()
                price_from = Price.objects.filter(training=training, quantity_from__lte=participant_count).order_by(
                    '-quantity_from').first()

                total_salary = 0

                if price_to and participant_count <= price_to.quantity_to:
                    total_salary += participant_count * price_to.price_to
                elif price_from:
                    total_salary += participant_count * price_from.price_from

                ws.append([
                    f'{trainer.first_name} {trainer.last_name}',
                    training.name,
                    attendance.created_date.strftime('%Y-%m-%d'),
                    f'{attendance.recording_day} {attendance.recording_date.strftime("%H:%M")}-{attendance.recording_date.strftime("%H:%M")}',
                    participant_count,
                    total_salary
                ])

    if trainer_ids and len(trainer_ids) == 1:
        trainer = trainers.first()
        trainer_name = f'{trainer.first_name}_{trainer.last_name}'.replace(' ', '_')
        filename = f'{trainer_name}_data.xlsx'
    else:
        filename = 'trainers_data.xlsx'

    safe_filename = urllib.parse.quote(filename)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{safe_filename}'
    wb.save(response)
    return response


class PriceInline(admin.TabularInline):
    model = Price
    extra = 1
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
    actions = ['export_all_trainers', 'export_selected_trainers']
    action_form = DateRangeForm

    def export_all_trainers(self, request, queryset):
        total_trainers = Trainer.objects.count()
        selected_trainers = queryset.count()

        if selected_trainers != total_trainers:
            self.message_user(request, "Пожалуйста, выберите всех тренеров для экспорта всех данных.",
                              level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        return export_trainers_data_to_excel(request, start_date=start_date, end_date=end_date)

    def export_selected_trainers(self, request, queryset):
        if queryset.count() == 0:
            self.message_user(request, "Пожалуйста, выберите одного или более тренеров для экспорта их данных.",
                              level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())

        trainer_ids = queryset.values_list('id', flat=True)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        return export_trainers_data_to_excel(request, trainer_ids=trainer_ids, start_date=start_date, end_date=end_date)

    export_all_trainers.short_description = 'Экспорт всех данных о всех тренерах в Excel'
    export_selected_trainers.short_description = 'Экспорт данных выбранных тренеров в Excel'

    list_display = ('first_name', 'last_name', 'phone_number', 'trainertg_id')
    search_fields = ('first_name', 'last_name', 'phone_number', 'trainertg_id')
    list_filter = ('first_name', 'last_name')
    ordering = ('last_name', 'first_name')


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'start_date', 'end_date')
    search_fields = ('name', 'trainer__first_name', 'trainer__last_name')
    list_filter = ('start_date', 'end_date')
    ordering = ('start_date',)
    inlines = [TrainingScheduleInline, PriceInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('training', 'attend_count', 'recording_day', 'recording_date', 'created_date', 'update_date')
    search_fields = ('training__name', 'recording_day')
    list_filter = ('recording_date', 'recording_day')
    ordering = ('recording_date',)
