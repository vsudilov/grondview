from django import forms
from django.forms.widgets import RadioSelect, CheckboxInput


class ObjectQueryForm(forms.Form):
  coords = forms.CharField(
              widget=forms.TextInput(
                  attrs={'placeholder':"Decimal or hh:mm:ss dd:mm:ss",'autofocus':'autofocus',
                          'class':'coordinates_input'}),
              label="Coordinates"
              )

  radius = forms.FloatField(
              widget=forms.TextInput(
                  attrs={'value':"1.0",'min': '1.0', 'max': '300','class':'radius_input'}),
              label="Radius"
              ) 
  
  include_user_detections = forms.FloatField( 
              widget=CheckboxInput(
                attrs={'checked':True}),
              label = "Include user detections")
