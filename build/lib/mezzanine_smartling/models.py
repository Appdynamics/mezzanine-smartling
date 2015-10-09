import os
import re
import datetime
import json
import jsonfield
import shutil
import logging
import importlib
import settings
from collections import OrderedDict
from tempfile import mkdtemp
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields import DateTimeField, DateField
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.contrib.sites.models import Site
from mezzanine.core.models import OrderableBase
from mezzanine.utils.sites import current_site_id
from .smartlingapi import upload_smartling_file
#from south.modelsinspector import add_introspection_rules
from mezzanine_smartling import manager as page_translations_manager, get_registered_models

logger = logging.getLogger(__name__)

def import_translatable_models():
    im = []
    for p in settings.TRANSLATABLE_PACKAGES:
       m = importlib.import_module(p)
       im.append(m)
    return im

translatable_modules = import_translatable_models()

def get_model_name(content_model):
    for tm in translatable_modules:
        for mod in dir(tm.models):
            if content_model.lower() == mod.lower():
                return mod
    return ''


def get_content_model(cont_model):
    model_name = get_model_name(cont_model)
    if model_name == 'RichTextPage':
        return RichTextPage
    if cont_model == 'link':
        return Link
    for tm in translatable_modules:
        try:
            content_model = getattr(tm.models, model_name)
        except AttributeError:
            pass
    return content_model


class TranslatablePageMixin(object):

    def serialized_json(self, obj=None):
        page_json = {}
        if obj:
            page = obj
        else:
            page = self

        for attr in page._meta.get_all_field_names():
            if attr in page.__dict__:
                value = page.__dict__[attr]
                if isinstance(value, datetime.datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S.%f")
                if isinstance(value, datetime.date):
                    value = value.strftime("%Y-%m-%d")
                if isinstance(value, ImageFieldFile):
                    value = value.name
                page_json[attr] = value
        return page_json

    def related_smartling_json(self):
        related = self.get_all_related_objects()
        related_model_names = []
        trans_json = {}
        untranslated_models = []
        if hasattr(settings, 'TRANSLATABLE_UNTRANSLATED_RELATEDMODELNAMES'):
            for rmname in settings.TRANSLATABLE_UNTRANSLATED_RELATEDMODELNAMES:
                untranslated_models.append(rmname)
        for model, foreign_key_name, foreign_key_type in related:
            if model._meta.object_name not in untranslated_models:
                related_model_names.append(model._meta.object_name)
                try:
                    blocks = model.objects.filter(**{foreign_key_name: self.id, 'site': current_site_id()})
                except TypeError:
                    blocks = model.objects.filter(**{foreign_key_name: self.id})
                jlst = []
                for b in blocks:
                    block_json = self.serialized_json(b)
                    if 'id' in block_json:
                        del block_json['id']
                    related_json = self.create_follow_json(b)
                    if related_json:
                        block_json['related'] = related_json
                    jlst.append(block_json)
                trans_json[model._meta.object_name] = jlst
        for field in self._meta.many_to_many:
            rel_model = field.related.parent_model
            if rel_model._meta.object_name not in related_model_names:
                related_objects = getattr(self, field.name).select_related()
                jlst = []
                for ro in related_objects:
                    block_json = self.serialized_json(ro)
                    if 'id' in block_json:
                        del block_json['id']
                    jlst.append(block_json)
                trans_json[rel_model._meta.object_name] = jlst
        return trans_json

    def get_follow_relationships(self, obj):
        return page_translations_manager.follow_relationships([obj])

    def create_follow_json(self, obj):
        def remove_untrans_keys(kobj):
            for k in kobj.keys():
                if re.search('_cache|_state|^id$', k):
                    del kobj[k]
            return kobj
        follow_rels = self.get_follow_relationships(obj)
        follow_json = {}
        for fr in follow_rels:
            if fr.__class__ != obj.__class__:
                ojson = fr.__dict__
                follow_json[obj._meta.object_name] = remove_untrans_keys(ojson)
        return follow_json

    def smartling_json(self):
        trans_json = OrderedDict()
        trans_json[self._meta.object_name] = [self.serialized_json()]
        # if current_site_id() == 1:
        #     if 'slug' in trans_json[self._meta.object_name][0]:
        #         trans_json[self._meta.object_name][0]['original_url'] = trans_json[self._meta.object_name][0]['slug']
        trans_json['page_type'] = self._meta.object_name
        trans_json.update(self.related_smartling_json())
        trans_path = self.create_translation_path(trans_json)
        smrt_json = self.create_smartling_json(trans_path, trans_json)
        import pprint;pprint.pprint(smrt_json) # Remove
        return smrt_json

    def upload_to_smartling(self):
        smrt_json = self.smartling_json()
        fname = '%s.json' % smrt_json[self._meta.object_name][0]['title']
        try:
            tmpdir = mkdtemp()
            with open(os.path.join(tmpdir, fname), 'w') as f:
                f.write(json.dumps(smrt_json, indent=4))
            upload_smartling_file(tmpdir + '/', fname)
        finally:
            try:
                shutil.rmtree(tmpdir)
            except OSError as exc:
                logger.error(exc)

    def get_untranslated_field_names(self, trans_json):
        model_field_names = {}
        for key_model_type in trans_json.keys():
            field_names = []
            try:
                obj = get_content_model(key_model_type)
                if isinstance(obj, ModelBase) or isinstance(obj, OrderableBase):
                    for i in obj._meta.fields:
                        try:
                            i.get_choices()
                            field_names.append(i.name)
                        except Exception as ie:
                            for cls in [ImageField, DateTimeField, DateField, models.FileField]:
                                if i.__class__ is cls:
                                    field_names.append(i.name)
                            logger.error(ie)
            except Exception as e:
                logger.error(e)
            model_field_names[key_model_type] = field_names
            if hasattr(settings, 'TRANSLATABLE_UNTRANSLATED_FIELDNAMES'):
                for fname in settings.TRANSLATABLE_UNTRANSLATED_FIELDNAMES:
                    model_field_names[key_model_type].append(fname)
        return model_field_names

    def create_translation_path(self, trans_json):
        untrans_model_field_names = self.get_untranslated_field_names(trans_json)
        untrans_models = []
        # TODO: Make these model name package specific
        if hasattr(settings, 'TRANSLATABLE_UNTRANSLATED_MODELNAMES'):
            for mname in settings.TRANSLATABLE_UNTRANSLATED_MODELNAMES:
                untrans_models.append(mname)
        translate = []
        for model_name, model_objs in trans_json.iteritems():
            if type(model_objs) == list and len(model_objs) > 0:
                first_mod = model_objs[0]
                for field, val in first_mod.iteritems():
                    if field not in untrans_model_field_names[model_name] and model_name not in untrans_models and not isinstance(val, bool):
                            translate.append('/%s/%s' % (model_name, field))
        return translate

    def create_smartling_json(self, trans_path, trans_json):
        json_doc = OrderedDict()
        json_doc['smartling'] = OrderedDict()
        json_doc['smartling']['translate_mode'] = 'custom'
        json_doc['smartling']['translate_paths'] = trans_path
        for k, v in trans_json.iteritems():
            json_doc[k] = v
        return json_doc

    def get_all_related_objects(self):
        related_models = []
        for rel in self._meta.get_all_related_objects():
            if rel.model._meta.object_name != 'Page':
                related_field = self.get_related_model_and_field(self, rel.model)
                related_models.append(related_field)
        return related_models

    def get_related_model_and_field(self, parent_model, foreign_model):
        for field in foreign_model._meta.fields:
            try:
                if isinstance(parent_model, field.rel.to):
                    return (foreign_model, field.name, field.rel.to)
            except AttributeError:
                pass
        return None

#add_introspection_rules([], ["^page_translations\.models\.LongJSONField"])


class LongJSONField(jsonfield.JSONField):
    def db_type(self, connection):
        return 'longtext'


class SmartlingTranslation(models.Model):
    page_uri = models.CharField(blank=False, max_length=1024)
    locale = models.CharField(blank=False, max_length=1024)
    json_doc = LongJSONField()
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    site = models.ForeignKey(Site, editable=False, related_name='smartlingtranslation_site')

    def __unicode__(self):
        return self.page_uri

