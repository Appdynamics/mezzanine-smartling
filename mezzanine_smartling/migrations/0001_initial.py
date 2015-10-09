# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mezzanine_smartling.models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_auto_20150527_1555'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SmartlingTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_uri', models.CharField(max_length=1024)),
                ('locale', models.CharField(max_length=1024)),
                ('json_doc', mezzanine_smartling.models.LongJSONField(default=dict)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('site', models.ForeignKey(related_name='smartlingtranslation_site', editable=False, to='sites.Site')),
            ],
        ),
        migrations.CreateModel(
            name='TestModel',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('rel_canonical', models.CharField(max_length=2048, blank=True)),
                ('compact_header', models.BooleanField(default=False)),
                ('hero_logo_image_alt', models.CharField(max_length=512, verbose_name=b'Image Alt Tag', blank=True)),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=('pages.page',),
        ),
    ]
