# Generated by Django 3.2.7 on 2024-08-12 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0173_auto_20240807_0920'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='center',
            options={'verbose_name': 'centro'},
        ),
        migrations.AddField(
            model_name='center',
            name='country',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='center',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='center',
            name='location',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='center',
            name='longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='center',
            name='region',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='entryform',
            name='center_index',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.center'),
        ),
        migrations.AddField(
            model_name='entryform',
            name='company_laboratory',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.CreateModel(
            name='CustomerCenter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.center')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.customer')),
            ],
        ),
        migrations.AddField(
            model_name='customer',
            name='center',
            field=models.ManyToManyField(blank=True, through='backend.CustomerCenter', to='backend.Center'),
        ),
    ]
