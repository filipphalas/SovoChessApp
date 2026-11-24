from django.conf import settings


def site_info(request):
    # so every template can use {{ site.operator }}, {{ site.contact_email }} etc
    return {'site': getattr(settings, 'SITE_INFO', {})}
