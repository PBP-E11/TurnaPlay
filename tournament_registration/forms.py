from django.core.exceptions import ValidationError
from django import forms
from .models import TournamentRegistration, TeamMember, GameAccount
from user_account.models import UserAccount

class TeamNameForm(forms.ModelForm):
    class Meta:
        model = TournamentRegistration
        fields = ['team_name']

class MemberForm(forms.Form):
    username = forms.CharField(max_length=60)
    game_account = forms.ModelChoiceField(queryset=GameAccount.objects.none())

    def __init__(self, *args, user=None, readonly=True, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['game_account'].queryset = GameAccount.objects.filter(user=user)
        # Set readonly (or not)
        self.fields['username'].widget.attrs['readonly'] = readonly
        self.fields['game_account'].widget.attrs['readonly'] = readonly

        # Make this field show the ingame_name instead of debug string representation
        self.fields['game_account'].label_from_instance = lambda obj: obj.ingame_name

class LeaderForm(MemberForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['readonly'] = True
