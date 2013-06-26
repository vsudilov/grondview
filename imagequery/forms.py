from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple

class ImageQueryForm(forms.Form):
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'input-block-level'}),
              label="Coordinates"
              )


  radius_arcmin = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"5.4",'class':'input-block-level'}),
              label="Search radius (arcminutes)"
              ) 
  
