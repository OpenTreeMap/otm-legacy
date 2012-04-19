from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import SiteProfileNotAvailable
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.localflavor.us.forms import USZipCodeField
from django_reputation.models import Reputation

def get_profile_model():
    """
    Return the model class for the currently-active user profile
    model, as defined by the ``AUTH_PROFILE_MODULE`` setting. If that
    setting is missing, raise
    ``django.contrib.auth.models.SiteProfileNotAvailable``.
    
    """
    if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or \
           (not settings.AUTH_PROFILE_MODULE):
        raise SiteProfileNotAvailable
    profile_mod = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))
    if profile_mod is None:
        raise SiteProfileNotAvailable
    return profile_mod


def get_profile_form():
    """
    Return a form class (a subclass of the default ``ModelForm``)
    suitable for creating/editing instances of the site-specific user
    profile model, as defined by the ``AUTH_PROFILE_MODULE``
    setting. If that setting is missing, raise
    ``django.contrib.auth.models.SiteProfileNotAvailable``.
    
    """
    profile_mod = get_profile_model()
    class _ProfileForm(forms.ModelForm):
        email = forms.EmailField(widget=forms.TextInput(),label="Email address",required=False)
        zip_code = USZipCodeField(required=False)
        class Meta:
            model = profile_mod
            # planning to remove volunteer attr..
            exclude = ('user','volunteer',) # User will be filled in by the view.

        def clean_email(self):
            """
            Validate that the supplied email address is unique for the
            site.
            
            """
            if User.objects.filter(email__iexact=self.cleaned_data['email']):
                raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
            return self.cleaned_data['email']

    return _ProfileForm

def get_reputation_change_amount_for_action(action, sub_action=None):
    if action not in settings.REPUTATION_SCORES.keys():
        raise Exception('The action "%s" does not have a score assigned in settings. Actions configured in REPUTATION_SCORES: %s', {action, settings.REPUTATION_SCORES.keys()})

    if sub_action is None:
        if isinstance(settings.REPUTATION_SCORES[action], int):
            return settings.REPUTATION_SCORES[action]
        else:
            raise Exception('A sub action must be specified for action "%s". Sub actions configured for %s in REPUTATION_SCORES: %s', (action, action, settings.REPUTATION_SCORES[action].keys()))
    else:
        sub_action_scores = settings.REPUTATION_SCORES[action]
        if type(sub_action_scores).__name__ == 'dict':
            if sub_action in sub_action_scores.keys():
                return sub_action_scores[sub_action]
            else:
                raise Exception('The sub action "%s" for "%s" does not have a score assigned in settings. Sub actions configured for "%s" in REPUTATION_SCORES: %s', {sub_action, action, action, sub_action_scores.keys()})
        else:
            raise Exception('The action %s does not have any sub actions assigned in settings' % action)

def change_reputation_for_user(user, action, model_object, sub_action=None, change_initiated_by_user=None):
    if user is None:
        raise Exception('The user argument cannot be none')

    if action is None:
        raise Exception('The action argument cannot be none')

    if model_object is None:
        raise Exception('The model_object argument cannot be none')

    if change_initiated_by_user is None:
        change_initiated_by_user = user

    reputation_change_amount = get_reputation_change_amount_for_action(action, sub_action)

    Reputation.objects.log_reputation_action(user, change_initiated_by_user, action, reputation_change_amount, model_object)

    return reputation_change_amount