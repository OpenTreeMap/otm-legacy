from django.conf import settings

def gkey(request):
    """
    """
    if request.META['SERVER_PORT'] == 80:
        return {'GKEY':settings.GOOGLE_API_KEY}
    else:
        return {'GKEY':settings.GOOGLE_API_DEV_KEY}

def tc_url(request):
    """
    """
    return {'TC_URL':settings.TC_URL}
