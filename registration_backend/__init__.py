from django import forms
from django.core.exceptions import ObjectDoesNotExist

from registration.backends.default import DefaultBackend
from registration.forms import RegistrationForm,RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
from profiles.models import UserProfile
from django.db import transaction
from treemap.localization import PostalCodeField

class TreeRegistrationForm(RegistrationForm):
    volunteer = forms.BooleanField(required=False)
    updates = forms.BooleanField(required=False)
    first_name = forms.RegexField(regex=r'^\w',
                                max_length=30,
                                widget=forms.TextInput(),
                                label=_("First Name"),
                                error_messages={ 'invalid': _("This value must contain only letters") },
                                required=False)
    last_name = forms.RegexField(regex=r'^\w',
                                max_length=30,
                                widget=forms.TextInput(),
                                label=_("Last Name"),
                                error_messages={ 'invalid': _("This value must contain only letters") },
                                required=False)
    zip_code = PostalCodeField(required=False)
    photo = forms.ImageField(required=False)


class TreeBackend(DefaultBackend):

    def get_form_class(self, request):
        return TreeRegistrationForm

    # also possible to catch signal to allow not having to
    # mix profiles app and registration app
    # http://docs.djangoproject.com/en/dev/topics/auth/#storing-additional-information-about-users
    # but since we are already extending registration
    # through a custom backend why not...
    @transaction.commit_on_success
    def register(self, request, **kwargs):
        new_user = super(TreeBackend,self).register(request, **kwargs)
        new_user.first_name = kwargs['first_name']
        new_user.last_name = kwargs['last_name']
        new_user.save()
        try:
            profile = new_user.get_profile()
        except:
            profile = UserProfile(user=new_user)
        profile.zip_code = kwargs.get('zip_code')
        profile.volunteer = kwargs.get('volunteer')
        profile.updates = kwargs.get('updates')
        profile.photo = kwargs.get('photo')
        profile.save()
        return new_user
