# Generated by Django 2.0.3 on 2020-09-08 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0090_auto_20200904_1322'),
    ]

    operations = [
        migrations.CreateModel(
            name='Research',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=250, null=True, verbose_name='Código')),
                ('name', models.CharField(blank=True, max_length=250, null=True, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('status', models.BooleanField(default=False, verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Estudio',
                'verbose_name_plural': 'Estudios',
            },
        ),
        migrations.AlterModelOptions(
            name='emailccto',
            options={'verbose_name': 'Destinatario copia para Plantilla Email', 'verbose_name_plural': 'Destinatarios copia para Plantilla Email'},
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='cc',
            field=models.ManyToManyField(blank=True, to='backend.EmailCcTo', verbose_name='Copia para'),
        ),
    ]
