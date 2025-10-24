from django.core.exceptions import ValidationError
from django import forms
from tournaments.models import Tournament
from .models import TournamentRegistration, TeamMember, GameAccount
from user_account.models import UserAccount

class TeamNameForm(forms.ModelForm):
    class Meta:
        model = TournamentRegistration
        fields = ['team_name']


class MemberForm(forms.ModelForm):
    # Hidden fields for internal logic
    team = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = TeamMember
        fields = ['game_account', 'team']

    def __init__(self, *args, **kwargs):
        user: UserAccount = kwargs.pop('user', None)
        team: TournamentRegistration = kwargs.pop('team', None)
        tournament: Tournament = kwargs.pop('tournament', None)
        super().__init__(*args, **kwargs)

        # Always hide team ID from template (assigned automatically)
        if team:
            self.fields['team'].initial = str(team.id)

        # Only show game accounts belonging to the user and matching the tournament’s game
        if user and (tournament or team):
            if tournament and team:
                if team.tournament != tournament:
                    return ValueError('Tournament inconsistent with Team')
            if team:
                tournament = team.tournament
            game = tournament.tournament_format.game
            self.fields['game_account'].queryset = GameAccount.objects.filter(
                user=user,
                game=game,
                active=True,
            )
        else:
            self.fields['game_account'].queryset = GameAccount.objects.none()

        # Show ingame name only, not "(game)"
        self.fields['game_account'].label_from_instance = lambda obj: obj.ingame_name

