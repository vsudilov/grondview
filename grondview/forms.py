from django import forms

class LoginForm(forms.Form):
  username = forms.CharField()
  passwd = forms.CharField(widget=forms.PasswordInput(render_value=False), label="Password")

