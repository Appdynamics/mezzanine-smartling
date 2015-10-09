import datetime
from django.contrib import admin
from django.contrib.sites.models import Site
from mezzanine.pages.models import Page
from mezzanine.utils.sites import current_site_id
from .models import get_content_model, SmartlingTranslation
from mezzanine_smartling import manager as page_translations_manager, get_registered_models


class ApprovedSmartlingTranslation(object):
    def __init__(self, smrt_json):
        self.smrt_json = smrt_json
        self.page_type = self.smrt_json['page_type']
        self.page_content_model = get_content_model(self.smrt_json['page_type'])
        self.page_json = self.smrt_json[self.page_type][0]

        self.related_object_names = [o for o in self.smrt_json.keys() if o not in ['smartling', self.page_type]]
        self.page = None

        if 'id' in self.page_json:
            del self.page_json['id']

        self.convert_fields_to_date(self.page_json)

    def convert_fields_to_date(self, attrs):
        date_formats = [
            '%m.%d.%Y %H:%M:%S',
            '%d.%m.%Y %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%m-%d-%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
        ]
        for a, v in attrs.iteritems():
            for dte in date_formats:
                try:
                    attrs[a] = datetime.datetime.strptime(v[:v.rfind('.')], dte)
                except AttributeError:
                    pass
                except ValueError:
                    pass
                except UnicodeEncodeError:
                    pass

    def insert_trans_page(self):
        # Ignore gen_description field
        # It causes the description field to not be encoded to unicode
        if 'gen_description' in self.page_json:
            self.page_json['gen_description'] = False
        if type(self.page_content_model.__base__) != type(Page):
            self.page_json['site_id'] = current_site_id()
        self.page = self.page_content_model(**self.page_json)
        self.page.save()

    def upsert_relational_objects(self):
        for related_obj_name in self.related_object_names:
            if related_obj_name == 'page_type':
                continue
            related_obj_model = get_content_model(related_obj_name)
            # Is it a m2m object?
            m2m_field_names = self.many_to_many_field_names(related_obj_model)
            if len(m2m_field_names) > 0:
                for m2m_fldname in m2m_field_names:
                    for m2m_json_obj in self.smrt_json[related_obj_name]:
                        # Attempt to find m2m object that exists
                        if 'id' in m2m_json_obj:
                            del m2m_json_obj['id']
                        m2m_obj = self.find_many_to_many_object(m2m_json_obj, related_obj_model)
                        if not m2m_obj:
                            site = Site.objects.get(id=current_site_id())
                            try:
                                m2m_json_obj['site'] = site
                                m2m_obj = related_obj_model(**m2m_json_obj)
                                m2m_obj.save()
                                del m2m_json_obj['site']
                            except TypeError:
                                del m2m_json_obj['site']
                                m2m_obj = related_obj_model(**m2m_json_obj)
                                m2m_obj.save()
                        getattr(self.page, m2m_fldname).add(m2m_obj)
            else:
                foreign_key_field = self.get_foreign_key_field(related_obj_model)
                for foreign_json_object in self.smrt_json[related_obj_name]:
                    foreign_json_object[foreign_key_field] = self.page
                    self.upsert_follow_objects(foreign_json_object, related_obj_model)
                    try:
                        foreign_json_object['site'] = current_site_id()
                        fk_obj = related_obj_model(**foreign_json_object)
                        fk_obj.save()
                    except TypeError:
                        del foreign_json_object['site']
                        fk_obj = related_obj_model(**foreign_json_object)
                        fk_obj.save()
                    if foreign_key_field in foreign_json_object:
                        del foreign_json_object[foreign_key_field]
                    self.remove_related_follow_fields(foreign_json_object, related_obj_model)

    def upsert_follow_objects(self, block_json, related_obj_model):
        if 'related' in block_json:
            related_json = block_json['related']
            del block_json['related']
            # Assume that there is only one relation for inheritance
            for model_name, attrs in related_json.iteritems():
                content_model = get_content_model(model_name)
                obj = content_model(**related_json[model_name])
                obj.save()
            self.add_related_follow_field(block_json, related_obj_model, obj)

    def add_related_follow_field(self, block_json, related_obj_model, follow_obj):
        follow_field = self.get_follow_field(related_obj_model)
        block_json[follow_field] = follow_obj

    def remove_related_follow_fields(self, block_json, related_obj_model):
        follow_field = self.get_follow_field(related_obj_model)
        if follow_field and follow_field in block_json:
            del block_json[follow_field]

    def get_follow_field(self, block_obj):
        adapter = page_translations_manager.get_adapter(block_obj)
        if hasattr(adapter, 'follow'):
            return adapter.follow[0]
        return None

    def many_to_many_field_names(self, field_model):
        m2m_fields = []
        for field in self.page_content_model._meta.many_to_many:
            if field_model._meta.object_name == field.related.parent_model._meta.object_name:
                m2m_fields.append(field.name)
        return m2m_fields

    def update_page_fields(self, existing_page):
        for k, v in existing_page.__dict__.iteritems():
            if k == '_order':
                continue
            try:
                existing_page.__dict__[k] = self.page_json[k]
            except KeyError:
                pass

    def find_many_to_many_object(self, m2m_json_obj, related_object_model):
        title_field_name = related_object_model.__unicode__.func_code.co_names[0]
        try:
            found_obj = related_object_model.objects.get(**{title_field_name: m2m_json_obj[title_field_name], 'site': current_site_id()})
        except related_object_model.MultipleObjectsReturned as e:
            found_obj = None
        except related_object_model.DoesNotExist as e:
            found_obj = None
        return found_obj

    def get_foreign_key_field(self, foreign_model):
        for field in foreign_model._meta.fields:
            try:
                if self.page_content_model._meta.object_name == field.rel.to._meta.object_name:
                    return field.name
            except AttributeError:
                pass
        return None


class TranslationApprovedFilter(admin.SimpleListFilter):
    title = 'Translations approved'
    parameter_name = 'approve'

    def lookups(self, request, model_admin):
        return (
            ('True', 'Approved'),
            ('False', 'Not Approved'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(approved=True)

        if self.value() == 'False':
            return queryset.filter(approved=False)


def save_page_translation(queryset):
    for o in queryset:
        app_trans = ApprovedSmartlingTranslation(o.json_doc)
        app_trans.insert_trans_page()
        app_trans.upsert_relational_objects()
        # Set approved
        o.approved = True
        o.save()


def approve_translation(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    qs = queryset.filter(id__in=selected)
    msg = []
    for obj in qs:
        msg.append(obj.page_uri)
    m = ', '.join(msg)
    m += ' saved.'
    save_page_translation(queryset)
    modeladmin.message_user(request, m)
approve_translation.short_description = "Approve translation (Save page with translated content)"


class SmartlingTranslationAdmin(admin.ModelAdmin):
    actions = [approve_translation]
    list_filter = (TranslationApprovedFilter,)
    list_display = ['page_uri', 'created', 'approved']

    def queryset(self, request):
        if current_site_id() == 1:
            objs = SmartlingTranslation.objects.filter(Q(site=current_site_id()) | Q(site=None))
        else:
            objs = SmartlingTranslation.objects.filter(site=current_site_id())
        return objs

admin.site.register(SmartlingTranslation, SmartlingTranslationAdmin)

