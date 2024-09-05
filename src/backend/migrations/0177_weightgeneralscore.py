# Generated by Django 3.2.7 on 2024-08-26 18:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0176_auto_20240814_1442'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeightGeneralScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intensity', models.IntegerField()),
                ('weight', models.IntegerField()),
                ('resultOrgan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.resultorgan')),
                ('watersource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.watersource')),
            ],
        ),
    ]
