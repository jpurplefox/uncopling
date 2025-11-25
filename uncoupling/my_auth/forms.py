from django import forms


class MeliCallbackForm(forms.Form):
    code = forms.CharField(required=False, max_length=255)
    error = forms.CharField(required=False, max_length=255)

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        error = cleaned_data.get('error')
        if error:
            raise forms.ValidationError(f'Authorization failed: {error}')

        if not code:
            raise forms.ValidationError('No authorization code received')

        return cleaned_data
