from django import forms
from django.forms.widgets import RadioSelect, CheckboxInput


class ObjectQueryForm(forms.Form):
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'coordinates_input'}),
              label="Coordinates"
              )

  radius_arcsec = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"1.0",'min': '1.0', 'max': '300','class':'radius_input'}),
              label="Search radius (arcsec)"
              ) 
