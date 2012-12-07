from django.conf import settings

def PostalCodeField(*args, **kwargs):
    if settings.POSTAL_CODE_FIELD == "GBPostcodeField":
        from django.contrib.localflavor.uk.forms import UKPostcodeField
        return UKPostcodeField
    else:
        from django.contrib.localflavor.us.forms import USZipCodeField
        return USZipCodeField
