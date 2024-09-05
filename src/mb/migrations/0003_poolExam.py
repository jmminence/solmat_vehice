# Generated by Django 3.2.7 on 2023-08-11 01:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0161_methodology'),
        ('mb', '0002_pool'),
    ]

    operations = [
        migrations.AddField(
            model_name='pool',
            name='exams',
            field=models.ManyToManyField(through='mb.PoolExam', to='backend.Exam'),
        ),
        migrations.AlterField(
            model_name='pool',
            name='identification',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.identification'),
        ),
        migrations.AlterField(
            model_name='poolexam',
            name='pool',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mb.pool'),
        ),
    ]
