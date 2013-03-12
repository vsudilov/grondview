from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
  args = 'None'
  help = 'Populate the database'

  def handle(self,*args,**options):
    import _populate_db
    _populate_db.main()
