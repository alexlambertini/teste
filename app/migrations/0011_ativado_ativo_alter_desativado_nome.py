# Generated by Django 5.1.5 on 2025-03-21 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_desativado_ativado_alter_desativado_motivo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ativado',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='desativado',
            name='nome',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
