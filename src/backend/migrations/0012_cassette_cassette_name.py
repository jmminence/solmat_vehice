# Generated by Django 2.0.3 on 2018-05-25 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0011_cassette_entryform'),
    ]

    operations = [
        migrations.AddField(
            model_name='cassette',
            name='cassette_name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
