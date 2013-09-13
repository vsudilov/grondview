from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from grondview.settings import PROJECT_ROOT
import os

class Command(BaseCommand):
  option_list = BaseCommand.option_list + (
          make_option('--file',
          dest='picklefile',
          default=os.path.join(PROJECT_ROOT,'aggregate.pickle'),
          help='Define where the pickle will be saved on disk'),
      )

  help = 'Aggregates data in the database and pickles it'
  def handle(self,*args,**kwargs):
    import _aggregate
    _aggregate.main(*args,**kwargs)