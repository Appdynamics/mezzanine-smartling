=====
Mezzanine Smartling Translations
=====

Mezzanine Smartling Translations allows you to save and upload the 
Mezzanine Page and Django model contents to Smartling for translations. When the translation is finished the page is saved into an admin view in which it pends for site specific approval.

This packages works with both Mezzanine Page models and standard Django models.

Installation
------------
::
    pip install mezzanine-smartling


Quick start
-----------

1. Add "mezzanine_smarling" to your INSTALLED_APPS setting like this
::

    INSTALLED_APPS = (
        ...
        'mezzanine_smarling',
    )

2. Include the polls URLconf in your project urls.py like this
::

    (r'^/', include('mezzanine_smartling.urls')),

3. Run `python manage.py migrate` to create the Mezzanine Smartling models.

4. Add TranslatablePageMixin to your Page models
::

  from mezzanine_smartling.models import TranslatablePageMixin

  class MyPage(Page, TranslatablePageMixin):
      subheader = models.CharField(blank=True, max_length=256)

5. Add this code to you Model's admin save_model function
::

    class MyPageHTMLAdmin(PageAdmin):
        def save_model(self, request, obj, form, change):            
            if change and hasattr(obj, '_old_slug') and obj._old_slug != obj.slug:
              # _old_slug was set in PageAdminForm.clean_slug().
              new_slug = obj.slug or obj.generate_unique_slug()
              obj.slug = obj._old_slug
              obj.set_slug(new_slug)
            # Force parent to be saved to trigger handling of ordering and slugs.
            parent = request.GET.get("parent")
            if parent is not None and not change:
                obj.parent_id = parent
            obj.save()
            if '_translate' in request.POST:
                obj.upload_to_smartling()
                self.message_user(request, "Successfully uploaded to Smartling", level=messages.SUCCESS)

6. Add settings to settings.py
::

    SMARTLING_CALLBACK_URL = 'http://www.<yourliveserverdomain>.com/smartling_callback'
    TRANSLATABLE_PACKAGES = (
      # Package names that contain models to be translated
      'mypackage',
    )
    TRANSLATABLE_UNTRANSLATED_FIELDNAMES = (
        # Field names to be ignored in translations
        'content_model',
        'slug',
    )
    TRANSLATABLE_UNTRANSLATED_MODELNAMES = (
        # Model names to be ignored during translations
    )
    TRANSLATABLE_UNTRANSLATED_RELATEDMODELNAMES = (
        # Related models to be ignored in translations
    )
    TRANSLATEABLE_LOCALE_DOMAIN = {
        # Callback smartling local and top level domains
        'de-DE': '.de',
        'fr-FR': '.fr',
        'ja-JP': '.jp',
        'pt-BR': '.br',
        'it-IT': '.it',
        'es': '.es'
    }

Registering inherited related models
------------------------------------
from mezzanine_smartling import register as register_page_translation
::

    class MyPage(Page):
        pass

    class OrderModel(models.Model):
        order = models.CharField(blank=True, max_length=256)

        class Meta:
            abstract = True
            ordering = ['order', 'id']
            verbose_name = "Orderable Block"
            verbose_name_plural = "Orderable Blocks

    class RelationPageBlock(OrderModel):
        page = models.ForeignKey('MyPage')

    register_page_translation(RelationPageBlock, follow=['ordermodel_ptr'])

Flow Overview
-------------
.. image:: flow.png

Author
------

Craig Williams

- http://github.com/craigdub
- craig.williams@appdynamics.com
