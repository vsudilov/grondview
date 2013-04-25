from django.contrib import admin
from models import AstroSource
from models import Photometry


class AstroSourceAdmin(admin.ModelAdmin):
  search_fields = ['sourceID','RA','DEC']

class PhotometryAdmin(admin.ModelAdmin):
  search_fields = ['astrosource__sourceID','astrosource__RA','astrosource__DEC']

admin.site.register(AstroSource, AstroSourceAdmin)
admin.site.register(Photometry, PhotometryAdmin)


