# Generated by Django 4.2.13 on 2024-09-03 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trainer',
            old_name='trainertg_id',
            new_name='tg_id',
        ),
        migrations.AlterUniqueTogether(
            name='trainingschedule',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='phone_number',
            field=models.CharField(help_text='В международном формате без знака +', max_length=12, unique=True, verbose_name='Номер телефона'),
        ),
    ]
