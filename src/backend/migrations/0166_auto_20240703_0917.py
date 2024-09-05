# Generated by Django 3.2.7 on 2024-07-03 09:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0165_auto_20240510_1557'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cassette',
            name='entryform',
        ),
        migrations.RemoveField(
            model_name='cassette',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='cassette',
            name='samples',
        ),
        migrations.RemoveField(
            model_name='diagnostic',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='diagnosticdistribution',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='diagnosticintensity',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='emailtemplateattachment',
            name='template',
        ),
        migrations.DeleteModel(
            name='ExchangeRate',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='log',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='log',
            name='user',
        ),
        migrations.RemoveField(
            model_name='organlocation',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='pathology',
            name='organs',
        ),
        migrations.RemoveField(
            model_name='preinvoicefile',
            name='loaded_by',
        ),
        migrations.RemoveField(
            model_name='report',
            name='analysis',
        ),
        migrations.RemoveField(
            model_name='report',
            name='diagnostic',
        ),
        migrations.RemoveField(
            model_name='report',
            name='diagnostic_distribution',
        ),
        migrations.RemoveField(
            model_name='report',
            name='diagnostic_intensity',
        ),
        migrations.RemoveField(
            model_name='report',
            name='identification',
        ),
        migrations.RemoveField(
            model_name='report',
            name='images',
        ),
        migrations.RemoveField(
            model_name='report',
            name='organ',
        ),
        migrations.RemoveField(
            model_name='report',
            name='organ_location',
        ),
        migrations.RemoveField(
            model_name='report',
            name='pathology',
        ),
        migrations.RemoveField(
            model_name='report',
            name='sample',
        ),
        migrations.RemoveField(
            model_name='report',
            name='slice',
        ),
        migrations.RemoveField(
            model_name='reportfinal',
            name='analysis',
        ),
        migrations.RemoveField(
            model_name='slice',
            name='analysis',
        ),
        migrations.RemoveField(
            model_name='slice',
            name='cassette',
        ),
        migrations.RemoveField(
            model_name='slice',
            name='entryform',
        ),
        migrations.AlterModelOptions(
            name='emailtemplate',
            options={'verbose_name': 'email Adjunto', 'verbose_name_plural': 'email Adjuntos'},
        ),
        migrations.RemoveField(
            model_name='preinvoice',
            name='attached_files',
        ),
        migrations.RemoveField(
            model_name='preinvoice',
            name='invoice',
        ),
        migrations.DeleteModel(
            name='Cassette',
        ),
        migrations.DeleteModel(
            name='Diagnostic',
        ),
        migrations.DeleteModel(
            name='DiagnosticDistribution',
        ),
        migrations.DeleteModel(
            name='DiagnosticIntensity',
        ),
        migrations.DeleteModel(
            name='EmailTemplateAttachment',
        ),
        migrations.DeleteModel(
            name='Img',
        ),
        migrations.DeleteModel(
            name='Invoice',
        ),
        migrations.DeleteModel(
            name='Log',
        ),
        migrations.DeleteModel(
            name='OrganLocation',
        ),
        migrations.DeleteModel(
            name='Pathology',
        ),
        migrations.DeleteModel(
            name='PreinvoiceFile',
        ),
        migrations.DeleteModel(
            name='Report',
        ),
        migrations.DeleteModel(
            name='ReportFinal',
        ),
        migrations.DeleteModel(
            name='Slice',
        ),
    ]
