import badges
from django.contrib.auth.models import User
from profiles.models import UserProfile

class TrustedUser(badges.MetaBadge):
    id = 'trusteduser'
    model = User
    one_time_only = True
    
    title = "Trusted User"
    description = "Contibuted significantly to the site"
    level = "2"
    
    progress_start = 0
    progress_finish = 1000
    
    def get_user(self, instance):
        return instance

    def get_progress(self, user):
        return user.reputation.reputation
        
    def check_reputation(self, instance):
        if hasattr(instance, 'reputation'):
            if instance.reputation.reputation > 999:
                return True
        return False

class ProfileComplete(badges.MetaBadge):
    id = 'profilecomplete'
    model = UserProfile
    one_time_only = True
    
    title = "Profile Complete"
    description = "Profile is completed"
    level = "1"

    progress_start = 0
    progress_finish = 5
    
    def get_user(self, instance):
        return instance.user

    def get_progress(self, user):
        photo = 1 if user.get_profile().photo else 0
        f_name = 1 if user.first_name else 0
        l_name = 1 if user.last_name else 0
        zip = 1 if user.get_profile().zip_code else 0
        email = 1 if user.email else 0
        
        return photo + f_name + l_name + zip + email
    
    def check_photo(self, instance):
        return instance.photo
    
    def check_name(self, instance):
        return instance.first_name and instance.last_name
    
    def check_zip(self, instance):
        return instance.zip_code
    
    def check_email(self, instance):
        return instance.email