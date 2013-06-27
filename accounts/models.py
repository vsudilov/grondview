from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile

from objectquery.models import AstroSource

class UserProfile(UserenaBaseProfile):
  user = models.OneToOneField(User,
                              unique=True,
                              verbose_name=_('user'),
                              related_name='my_profile')
  tagged_sources = models.ManyToManyField(AstroSource)


class UserSourceNames(models.Model):
  user = models.OneToOneField(User,unique=True)
  astrosource = models.OneToOneField(AstroSource)
  name = models.CharField(max_length=30,null=True) #Optional name to add to the source

