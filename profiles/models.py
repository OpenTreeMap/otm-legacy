from operator import itemgetter
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _ # internationalization translate call
from django.contrib.gis.db import models
from treemap.models import Tree, Plot, TreeFlags, TreePhoto, TreePending, TreeStewardship, PlotStewardship
from django_reputation.models import UserReputationAction
from badges.models import Badge, BadgeToUser

import random

BOOLEAN_CHOICES =  (
                  (False, "No"),
                  (True, "Yes"),
                )

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name=_('Username'))
    # not going to use volunteer, comment at a good moment...
    volunteer = models.BooleanField("Volunteer Opportunities",choices=BOOLEAN_CHOICES,default=False)
    updates = models.BooleanField('I would like to receive occasional email updates and newsletters',choices=BOOLEAN_CHOICES,default=False)
    zip_code = models.CharField(max_length=20,null=True,blank=True)
    photo = models.ImageField(upload_to='photos',height_field=None, width_field=None, max_length=200,null=True,blank=True)
    site_edits = models.IntegerField(_('Site Edits (to track activity)'),default=0,editable=False)
    uid = models.IntegerField(_('Random User ID'),null=True,blank=True,editable=False)
    active = models.BooleanField(choices=BOOLEAN_CHOICES,default=True)

    def __unicode__(self):
        name = self.user.get_full_name()
        if name:
            return unicode("%s" % self.user.get_full_name())
        else:
            return unicode("%s" % self.user.username)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    # stripped-down recently_edited_trees to fix neighborhood display
    # in profiles/edit_profile.html and profile_detail.html

    def re_trees(self):
        trees = Tree.history.filter(last_updated_by=self.user, present=True).exclude(_audit_change_type="U",_audit_diff="").order_by('-last_updated')[:7]
        return(trees)

    def recently_edited_trees(self):
        trees = Tree.history.filter(last_updated_by=self.user, present=True).exclude(_audit_change_type="U",_audit_diff="").order_by('-last_updated')[:7]
        recent_edits = []
        for t in trees:
            recent_edits.append((t.species, t.date_planted, t.last_updated, t.id))
        return sorted(recent_edits, key=itemgetter(2), reverse=True)[:7]

    def recently_edited_plots(self):
        plots = Plot.history.filter(last_updated_by=self.user, present=True).exclude(_audit_change_type="U",_audit_diff="").order_by('-last_updated')[:7]
        recent_edits = []
        for p in plots:
            actual_plot = Plot.objects.get(pk=p.id)
            if actual_plot.current_tree():
                recent_edits.append((actual_plot.current_tree().species, actual_plot.current_tree().date_planted, p.last_updated, p.id))
            else:
                recent_edits.append(("", None, p.last_updated, p.id))
        return sorted(recent_edits, key=itemgetter(2), reverse=True)[:7]


    def recently_added_photos(self):
        return TreePhoto.objects.filter(reported_by=self.user, tree__present=True).order_by('-reported_by')[:7]

    def recently_changed_reputation(self):
        return UserReputationAction.objects.filter(user=self.user).order_by('-date_created')[:7]

    def recently_added_pends(self):
        return TreePending.objects.filter(submitted_by=self.user).order_by('-submitted')[:7]

    def recent_stewardship(self):
        tree_s = TreeStewardship.objects.filter(performed_by=self.user)[:7]
        plot_s = PlotStewardship.objects.filter(performed_by=self.user)[:7]
        recent_activity = []
        for t in tree_s:
            recent_activity.append((t.tree.species, t.get_activity(), t.performed_date, t.tree.plot.id))
        for p in plot_s:
            recent_activity.append((p.plot.current_tree().species, p.get_activity(), p.performed_date, p.plot.id))
        print recent_activity
        return sorted(recent_activity, key=itemgetter(2), reverse=True)[:7]


    def badges(self):
        return BadgeToUser.objects.filter(user=self)

    def badges_in_progress(self):
        return_badges = []
        for b in Badge.objects.all():
            if b.meta_badge.get_progress(self.user) > b.meta_badge.progress_start:
                if b.meta_badge.get_progress(self.user) < b.meta_badge.progress_finish:
                    return_badges.append((b, b.meta_badge.get_progress(self.user)))

        return return_badges

    def made_edit(self):
        self.site_edits += 1
        self.save()

    def username(self):
        return u"%s" % self.user.username

    def first_name(self):
        return u"%s" % self.user.first_name

    def last_name(self):
        return u"%s" % self.user.last_name

    def full_name(self):
        return u"%s %s" % (self.user.first_name, self.user.last_name)

    def email(self):
        return u"%s" % self.user.email

    def remove(self):
        return '<input type="button" value="Remove" onclick="location.href=\'%s/delete/\'" />' % (self.pk)

    remove.short_description = ''
    remove.allow_tags = True

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)

    def get_random_id(self):
        return random.randint(100000,999999)

    def account_activated(self):
        return self.user.is_active
    account_activated.boolean = True

    def account_diff(self):
        if self.user.is_active:
            return (self.user.date_joined - datetime.datetime.now())

    def save(self, force_insert=False, force_update=False, using='default'):
        if not self.id:
            self.uid = self.get_random_id()

        super(UserProfile, self).save()
