# Generated by Django 3.2.7 on 2022-05-24 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0022_auto_20220516_1358'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlindCarbonCopy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'BCC',
                'verbose_name_plural': 'BCCs',
            },
        ),
    ]
