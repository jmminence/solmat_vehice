# Generated by Django 3.2.7 on 2022-01-25 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0142_currency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='preinvoices',
        ),
        migrations.AddField(
            model_name='invoice',
            name='analysis_preinvoices',
            field=models.ManyToManyField(related_name='invoices', to='backend.AnalysisPreinvoice'),
        ),
    ]
