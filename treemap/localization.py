from django.conf import settings

if settings.POSTAL_CODE_FIELD == "GBPostcodeField":
   from django.contrib.localflavor.uk.forms import UKPostcodeField
   PostalCodeField = UKPostcodeField
else:
   from django.contrib.localflavor.us.forms import USZipCodeField
   PostalCodeField = USZipCodeField
