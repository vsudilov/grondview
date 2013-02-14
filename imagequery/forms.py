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

#  radius = forms.FloatField(
#              widget=forms.TextInput(
#                  attrs={'placeholder':"1.0\" - 900\'",'min': '0', 'max': '900'}),
#              label="Search radius"
#              )

#  unit_radius = forms.ChoiceField(
#              label="",
#              choices=[('arcmin','arcminutes'),
#                       ('arcsec','arcseconds')],
#              widget=forms.RadioSelect(attrs={'class':'unit'},
#              initial="arcmin")
#              )

  area = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"5.4",'min': '0.0167', 'max': '20','class':'area_input'}),
              label="Area"
              ) 

  unit_area = forms.ChoiceField(
              label="",
              choices=[('arcmin','arcminutes'),
                       ('arcsec','arcseconds')],
              widget=forms.Select(attrs={'class':'area_select-unit'}),
              initial="arcmin"
              )

  bands = forms.MultipleChoiceField(
              widget=CheckboxSelectMultiple(
                    attrs={'class' : 'bands_checkbox'}), 
              choices=BANDS,
              required=False,
              initial='r')

  dates = forms.CharField(
              widget=forms.DateInput(
                  attrs={'placeholder':"(Optional)",
                          'class':'dates_input'},
                  format="YYYY-MM-DD"),
              label="Date range",
              required=False,
              )
  
