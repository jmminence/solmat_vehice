# Generated by Django 2.1.15 on 2021-07-05 13:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0019_remove_process_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseProcessTree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lab.Case')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lab.CaseProcessTree')),
            ],
        ),
        migrations.RemoveField(
            model_name='caseprocess',
            name='case',
        ),
        migrations.RemoveField(
            model_name='caseprocess',
            name='process',
        ),
        migrations.RemoveField(
            model_name='examtree',
            name='exam',
        ),
        migrations.RemoveField(
            model_name='examtree',
            name='tree',
        ),
        migrations.RemoveField(
            model_name='processtree',
            name='process',
        ),
        migrations.RemoveField(
            model_name='processtree',
            name='tree',
        ),
        migrations.RemoveField(
            model_name='tree',
            name='process',
        ),
        migrations.RemoveField(
            model_name='process',
            name='case',
        ),
        migrations.AlterField(
            model_name='processunit',
            name='case_process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='process_units', to='lab.CaseProcessTree'),
        ),
        migrations.DeleteModel(
            name='CaseProcess',
        ),
        migrations.DeleteModel(
            name='ExamTree',
        ),
        migrations.DeleteModel(
            name='ProcessTree',
        ),
        migrations.DeleteModel(
            name='Tree',
        ),
        migrations.AddField(
            model_name='caseprocesstree',
            name='process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lab.Process'),
        ),
    ]
