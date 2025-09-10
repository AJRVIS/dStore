from django import forms

from store.models import Settlement

class UploadFileForm(forms.Form):
    file = forms.FileField()

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = ["amount_paid", "mode"]