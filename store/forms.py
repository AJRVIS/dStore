from django import forms

from store.models import Settlement, Customer

class UploadFileForm(forms.Form):
    file = forms.FileField()

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = ["amount_paid", "mode"]
        
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['dnumber', 'name', 'mobile']