from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple

BANDS = ( ('g', 'g'),
          ('r', 'r'),
          ('i', 'i'),
          ('z', 'z'),
          ('J', 'J'),
          ('H', 'H'),
          ('K', 'K'))

class ImageQueryForm(forms.Form):
  coords = forms.CharField(label="Coordinates")
  area = forms.FloatField(label="Area (arcminutes)")
  bands = forms.MultipleChoiceField(required=False,
          widget=CheckboxSelectMultiple(attrs={'class' : 'form-checkbox','checked' : 'checked'}), choices=BANDS)
  
