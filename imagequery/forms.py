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
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'coordinates_input'}),
              label="Coordinates"
              )


  radius = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"5.4",'min': '0.0167', 'max': '20','class':'radius_input'}),
              label="Search radius (arcminutes)"
              ) 

  dates = forms.CharField(
              widget=forms.DateInput(
                  attrs={'placeholder':"(Optional)",
                          'class':'dates_input'},
                  format="YYYY-MM-DD"),
              label="Date range",
              required=False,
              )
  
