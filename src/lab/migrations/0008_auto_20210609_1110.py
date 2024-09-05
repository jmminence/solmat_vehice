# Generated by Django 2.1.15 on 2021-06-09 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0007_auto_20210608_1354'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='laboratory',
            name='users',
        ),
        migrations.RemoveField(
            model_name='process',
            name='laboratories',
        ),
        migrations.RemoveField(
            model_name='process',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='processitem',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='processitem',
            name='process',
        ),
        migrations.RemoveField(
            model_name='processitem',
            name='unit',
        ),
        migrations.DeleteModel(
            name='Laboratory',
        ),
        migrations.DeleteModel(
            name='Process',
        ),
        migrations.DeleteModel(
            name='ProcessItem',
        ),
    ]
