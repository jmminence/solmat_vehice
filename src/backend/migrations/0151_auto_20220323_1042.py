# Generated by Django 3.2.7 on 2022-03-23 10:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0150_auto_20220321_1353'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='preinvoices',
        ),
        migrations.AddField(
            model_name='preinvoice',
            name='invoice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.invoice'),
        ),
    ]
