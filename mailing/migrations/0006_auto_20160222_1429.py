# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-22 14:29
from __future__ import unicode_literals

from django.db import migrations, models
import mailing.conf
import mailing.models.base
import mailing.models.options


class Migration(migrations.Migration):

    dependencies = [
        ('mailing', '0005_campaignstaticattachment_maildynamicattachment_mailstaticattachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='prefix_subject',
            field=models.BooleanField(default=True, help_text=mailing.conf.StringConfRef('SUBJECT_PREFIX', within='Wheter to prefix the subject with "{}" or not.'), verbose_name='prefix subject'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='template_file',
            field=models.FileField(blank=True, help_text='Leave blank to use mailing/{key}.html from within your template directories.', upload_to=mailing.models.base.templates_upload_to, verbose_name='template file'),
        ),
        migrations.AlterField(
            model_name='campaignstaticattachment',
            name='attachment',
            field=models.FilePathField(path=mailing.conf.StringConfRef('ATTACHMENTS_DIR'), recursive=True, verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='maildynamicattachment',
            name='attachment',
            field=models.FileField(upload_to=mailing.models.options.attachments_upload_to, verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='mailstaticattachment',
            name='attachment',
            field=models.FilePathField(path=mailing.conf.StringConfRef('ATTACHMENTS_DIR'), recursive=True, verbose_name='file'),
        ),
    ]
