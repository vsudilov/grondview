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
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus'}),
              label="Coordinates"
              )

  radius = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'placeholder':"1.0\" - 900\'",'min': '0', 'max': '900'}),
              label="Search radius"
              )

  unit = forms.ChoiceField(
              label="",
              choices=[('arcmin','arcminutes'),
                       ('arcsec','arcseconds')]
              )
  
  bands = forms.MultipleChoiceField(
              widget=CheckboxSelectMultiple(
                    attrs={'class' : 'form-checkbox','checked' : 'checked'}), 
              choices=BANDS,
              required=False,)
  
