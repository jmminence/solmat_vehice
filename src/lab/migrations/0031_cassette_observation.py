# Generated by Django 2.1.15 on 2021-10-01 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0030_unitproxy'),
    ]

    operations = [
        migrations.AddField(
            model_name='cassette',
            name='observation',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
