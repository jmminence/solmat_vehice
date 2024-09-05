# Generated by Django 2.0.3 on 2019-01-23 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0044_reportfinal_box_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='identification',
            name='extra_features_detail',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='identification',
            name='is_optimum',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='identification',
            name='observation',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='identification',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
