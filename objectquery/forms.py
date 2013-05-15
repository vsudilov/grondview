from django import forms
from django.forms.widgets import RadioSelect, CheckboxInput


CHOICES = {
  'n_bands': (
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5),
    (6,6),
    (7,7),
  )
}
class ObjectQueryForm(forms.Form):
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'coordinates_input'}),
              label="Coordinates"
              )

  radius_arcsec = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"5.0",'class':'radius_input'}),
              label="Search radius (arcsec)"
              )
  n_bands = forms.ChoiceField(widget=forms.Select,choices=CHOICES['n_bands'],
                              label="Seen in at least N bands:",
                              initial=2)

  forcedetect = forms.BooleanField(required=False, initial=False, label='Create a source at this exact position\n(this source ignores N bands criterion)') 
