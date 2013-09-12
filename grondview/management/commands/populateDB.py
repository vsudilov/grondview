from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from grondview.settings import PROJECT_ROOT, DEFAULT_FROM_EMAIL
from django.core.mail import send_mail
import os

class Command(BaseCommand):
  args = 'data_directory'
  option_list = BaseCommand.option_list + (
            make_option('--match-tolerance',
            dest='match_tolerance',
            default=0.5,
            help='Match tolerance in arcsec for resolving sources [0.5]'),
        )
  option_list += (
            make_option('--fits-regex',
            dest='fits_regex',
            default='GROND_._OB_ana.fits',
            help='Regex for finding GROND reduced images [GROND_._OB_ana.fits]'),
        )
  option_list += (
            make_option('--results-regex',
            dest='results_regex',
            default='GROND_._OB_ana.result',
            help='Regex for finding GROND resultfiles [GROND_._OB_ana.result]'),
        )
  option_list += (
            make_option('--bands',
            dest='bands',
            default='grizJHK',
            help='Bands to attempt processing on [grizJHK]'),
        )

  option_list += (
            make_option('--only-recent',
            dest='only_recent',
            default=None,
            help='Query only files with last modification time of X minutes'),
        )


  option_list += (
            make_option('--email-on-complete',
            dest='email',
            default=None,
            help='Notify when the script is complete'),
        )


  help = '''USAGE: manage.py populateDB path
            Populate the database. Adds data from GROND_?_OB_ana.fits and GROND_?_OB_ana.result found recursively from path.
            Overwrites sources/fields already in the database (SQL UPDATE).  
          '''
  help = help.strip()

  def handle(self,*args,**kwargs):
    import _populate_db
    try:
      _populate_db.main(*args,**kwargs)
      subject = "[grondview] Data incorporated successfully into the database"
      body = 'Thanks for your contribution!'
    except:
      subject = "[grondview] Error: All data were not loaded into the database"
      body = 'Sorry!'
      print self.help
      raise
    finally:
      if kwargs['email']:
        send_mail(subject, body, DEFAULT_FROM_EMAIL,[kwargs['email'],'vsudilov@mpe.mpg.de'], fail_silently=False)
      lockfile = os.path.join(PROJECT_ROOT,'populateDB.lock')
      if os.path.isfile(lockfile):
        with open(lockfile,'r') as f:
          pid = int(f.read())
        if pid == os.getpid():
          os.unlink(lockfile)








