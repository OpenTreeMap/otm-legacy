from django.conf import settings

def PostalCodeField(*args, **kwargs):
    if settings.POSTAL_CODE_FIELD == "GBPostcodeField":
        from django.contrib.localflavor.uk.forms import UKPostcodeField
        return UKPostcodeField(*args, **kwargs)
    else:
        from django.contrib.localflavor.us.forms import USZipCodeField
        return USZipCodeField(*args, **kwargs)

def convert_dbh_to_inches(dbh):
    return float(dbh) * settings.DBH_TO_INCHES_FACTOR

