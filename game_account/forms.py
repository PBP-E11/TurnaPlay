from django import forms
from .models import GameAccount

class GameAccountForm(forms.ModelForm):
    class Meta:
        model = GameAccount
        fields = ['game', 'ingame_name']

    def clean_ingame_name(self):
        name = self.cleaned_data['ingame_name'].strip()
        if not name:
            raise forms.ValidationError("In-game name can't be empty.")
        return name

    def clean(self):
        cleaned = super().clean()
        game = cleaned.get('game')
        name = cleaned.get('ingame_name')
        if game and name:
            # enforce uniqueness at form level for DBs that lack the unique constraints
            if GameAccount.objects.filter(game=game, ingame_name__iexact=name, active=True).exists():
                raise forms.ValidationError("This in-game name has already been used for this game.")
        return cleaned
