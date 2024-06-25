from django import forms
from django.contrib.admin.helpers import ActionForm

from training.models import Price, Trainer


class PriceToForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ['quantity_to', 'price_to']

    def clean(self):
        cleaned_data = super().clean()
        price_to = cleaned_data.get("price_to")

        if price_to is None:
            raise forms.ValidationError("Поле 'Цена до' должно быть заполнено.")

        return cleaned_data


class PriceFromForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ['quantity_from', 'price_from']

    def clean(self):
        cleaned_data = super().clean()
        price_from = cleaned_data.get("price_from")

        if price_from is None:
            raise forms.ValidationError("Поле 'Цена от' должно быть заполнено.")

        return cleaned_data


class TrainerActionForm(ActionForm):
    action = forms.ChoiceField(choices=[], required=True,)
    start_date = forms.DateField(required=False, label="Начальная дата", widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, label="Конечная дата", widget=forms.TextInput(attrs={'type': 'date'}))
