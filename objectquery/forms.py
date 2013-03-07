from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple


class ObjectQueryForm(forms.Form):
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'coordinates_input'}),
              label="Coordinates"
              )

  area = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"1.0 (arcseconds)",'min': '1.0', 'max': '180','class':'area_input'}),
              label="Area"
              ) 

  dates = forms.CharField(
              widget=forms.DateInput(
                  attrs={'placeholder':"(Optional)",
                          'class':'dates_input'},
                  format="YYYY-MM-DD"),
              label="Date range",
              required=False,
              )
  
