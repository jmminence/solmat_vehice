# Generated by Django 3.2.7 on 2022-05-16 13:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0151_auto_20220323_1042'),
        ('review', '0021_auto_20220513_1506'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisrecipient',
            name='grouper',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='review.grouper'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='grouper',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='final_attachments', to='review.grouper'),
        ),
        migrations.AddField(
            model_name='file',
            name='grouper',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='review.grouper'),
        ),
        migrations.AddField(
            model_name='finalreport',
            name='grouper',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='final_reports', to='review.grouper'),
        ),
        migrations.AddField(
            model_name='stage',
            name='grouper',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='review.grouper'),
        ),
        migrations.AlterField(
            model_name='analysisrecipient',
            name='analysis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='review.analysis'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='analysis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='final_attachments', to='review.analysis'),
        ),
        migrations.AlterField(
            model_name='file',
            name='analysis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='review.analysis'),
        ),
        migrations.AlterField(
            model_name='finalreport',
            name='analysis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='final_reports', to='review.analysis'),
        ),
        migrations.AlterField(
            model_name='grouper',
            name='name',
            field=models.CharField(blank=True, max_length=90, null=True),
        ),
        migrations.AlterField(
            model_name='stage',
            name='analysis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='backend.analysisform'),
        ),
    ]
