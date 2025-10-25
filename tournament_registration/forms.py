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
    class Meta:
        model = TeamMember
        fields = ['game_account', 'team']
        widgets = {
            'team': forms.HiddenInput(),
        }

    def __init__(self, *args, user: UserAccount = None, team: TournamentRegistration = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Only show game accounts belonging to the user and matching the tournament’s game
        if user and team:
            tournament = team.tournament
            self.fields['game_account'].queryset = _get_game_account(user, tournament)
        else:
            self.fields['game_account'].queryset = GameAccount.objects.none()

        # Show ingame name only, not "(game)"
        self.fields['game_account'].label_from_instance = lambda obj: obj.ingame_name

    def clean_game_account(self):
        return _clean_game_account(self)

class PreTeamMemberForm(forms.Form):
    """
    A plain form used *before* a Team (TournamentRegistration) exists.
    - Only validates game_account (ModelChoiceField).
    - Does NOT try to validate or touch TeamMember.team during form validation.
    - Use .save(team=team_instance, is_leader=...) after creating the team.
    """
    game_account = forms.ModelChoiceField(queryset=GameAccount.objects.none())

    def __init__(self, *args, user: UserAccount = None, tournament: Tournament = None, **kwargs):
        """
        user will be saved to display error for invalid ownership
        tournament is for limiting game_account options
        """
        super().__init__(*args, **kwargs)
        self.user = user

        # limit choices to current user's active accounts for this tournament's game
        if user and tournament:
            self.fields['game_account'].queryset = _get_game_account(user, tournament)
        else:
            # no user/tournament -> empty choices (safe)
            self.fields['game_account'].queryset = GameAccount.objects.none()

        # label shows ingame name only
        self.fields['game_account'].label_from_instance = lambda obj: obj.ingame_name

    def clean_game_account(self):
        return _clean_game_account(self)

    def save(self, *, team: TournamentRegistration = None, is_leader: bool = True, commit: bool = True) -> TeamMember:
        """
        Create a TeamMember instance. `team` must be a TournamentRegistration instance.
        This does NOT call model-form validation (we call `full_clean()` on the model before save).
        """
        if not self.is_valid():
            raise ValidationError("Form data invalid; cannot save.")

        # require a real team instance (not just an id) at save time
        if team is None or not isinstance(team, TournamentRegistration):
            raise ValueError("A TournamentRegistration instance must be provided to save the member.")

        game_account: GameAccount = self.cleaned_data['game_account']
        member = TeamMember(team=team, game_account=game_account, is_leader=is_leader)

        # model-level validation now that team exists
        member.full_clean()
        if commit:
            member.save()
        return member


def _get_game_account(user: UserAccount, tournament: Tournament):
    game = tournament.tournament_format.game
    return GameAccount.objects.filter(
        user=user,
        game=game,
        active=True,
    )

def _clean_game_account(self):
    game_account = self.cleaned_data.get('game_account')
    if game_account is None:
        raise ValidationError("Please select a game account.")
    # sanity: ensure selected account belongs to the user
    if self.user and game_account.user != self.user:
        raise ValidationError("Selected game account does not belong to you.")
    return game_account
