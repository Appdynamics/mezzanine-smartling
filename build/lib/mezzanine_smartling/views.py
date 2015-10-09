import json
import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse
from .models import SmartlingTranslation
from .smartlingapi import get_smartling_file


class ConfigurationError(Exception):
    """Exception thrown when configuration is wrong."""


class HttpResponseServerError(HttpResponse):
    status_code = 500

def smartling_callback(request):
    def resolve_locale(locale):
        """
        Example TRANSLATEABLE_LOCALE_DOMAIN
        TRANSLATEABLE_LOCALE_DOMAIN = {
            'de-DE': '.de',
            'fr-FR': '.fr',
            'ja-JP': '.jp',
            'pt-BR': '.br',
            'it-IT': '.it',
            'es': '.es'
        }
        """
        if not hasattr(settings, 'TRANSLATEABLE_LOCALE_DOMAIN'):
            raise ConfigurationError("Missing TRANSLATEABLE_LOCALE_DOMAIN in settings file.")
        locale_domain = settings.TRANSLATEABLE_LOCALE_DOMAIN
        try:
            site_id = get_site_id_by_domain_contains(locale_domain[locale])
        except KeyError as ke:
            raise ConfigurationError("Could not find a site that matches domain in TRANSLATEABLE_LOCALE_DOMAIN settings.")
        return site_id

    def get_site_id_by_domain_contains(domain):
        try:
            site = Site.objects.get(domain__contains=domain)
        except site.DoesNotExist as e:
            logger.error(e)
            return 1
        return site.id

    import pdb;pdb.set_trace()
    try:
        file_uri = request.GET.get('fileUri')
        locale = request.GET.get('locale')
        ret_contents = get_smartling_file(file_uri, locale)
        json_content = ret_contents[0]
        json_content = json.loads(json_content)
        status_code = ret_contents[1]
        if status_code != 200:
            return HttpResponseServerError('<h1>Server Error (500)%s</h1>' % str(ret_contents))
        site_id = resolve_locale(locale)
        st = SmartlingTranslation(page_uri=file_uri.replace('.json', ''), locale=locale, json_doc=json_content, site_id=site_id)
        st.save()
    except Exception as e:
        return HttpResponseServerError()
    return HttpResponse(status=200)

