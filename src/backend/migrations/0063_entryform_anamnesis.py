# Generated by Django 2.0.3 on 2020-03-26 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0062_entryform_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='entryform',
            name='anamnesis',
            field=models.TextField(blank=True, null=True),
        ),
    ]
