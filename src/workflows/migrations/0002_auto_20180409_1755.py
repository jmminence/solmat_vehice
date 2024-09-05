# Generated by Django 2.0.3 on 2018-04-09 20:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=250, null=True)),
                ('type_permission', models.CharField(choices=[('w', 'Write'), ('a', 'Approve'), ('d', 'Deny'), ('r', 'Read')], max_length=1)),
                ('from_state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='permission_from_state', to='workflows.State')),
                ('to_state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='permission_to_state', to='workflows.State')),
            ],
        ),
        migrations.AddField(
            model_name='actor',
            name='permission',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflows.Permission'),
        ),
    ]
