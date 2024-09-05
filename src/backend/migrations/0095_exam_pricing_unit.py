# Generated by Django 2.0.3 on 2020-10-15 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0094_auto_20201014_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='pricing_unit',
            field=models.IntegerField(choices=[(1, 'Por órgano'), (2, 'Por pez')], default=1, verbose_name='Unidad de cobro'),
        ),
    ]
