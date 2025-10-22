import uuid
from tournaments.models import Tournament
from game_account.models import GameAccount
from django.db import models
from django.core.exceptions import ValidationError

class TournamentRegistration(models.Model):
    """
    Model representing a registration attempt (it can be complete or in progress), or in other words team details
    This module is managed by Fahri
    """

    # PK id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK tournament.id
    tournament = models.ForeignKey(
        Tournament,
        on_delete = models.CASCADE, # A registration is irrelevant if the tournament is void
        related_name = 'registrations',
        verbose_name = 'Associated Tournament',
    )

    # Team name
    team_name = models.CharField('Team Name', max_length=100)

    # Status
    class Status(models.TextChoices):
        INVALID = ('invalid', 'Invalid')
        VALID = ('valid', 'Valid')
        REGISTERED = ('registered', 'Registered')

    status = models.CharField(
        'Registration Status',
        max_length = 31,
        choices = Status.choices,
        default = Status.INVALID,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tournament', 'team_name'], name='unique_team_name_in_tournament')
        ]
        verbose_name = 'Tournament Registration'
        verbose_name_plural = 'Tournament Registrations'

    def __str__(self):
        return f'{self.team_name} ({self.tournament})'

class TeamMember(models.Model):
    """
    A many to one relation for members that has joined a team
    This module is managed by Fahri
    """

    # FK game_account.id
    game_account = models.ForeignKey(
        GameAccount,
        on_delete = models.CASCADE,
        related_name = 'joined_teams',
        verbose_name = 'Associated Game Account',
    )

    # FK tournament_registration.id
    team = models.ForeignKey(
        TournamentRegistration,
        on_delete = models.CASCADE,
        related_name = 'members',
        verbose_name = 'Associated Team',
    )

    # Is Leader
    is_leader = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def clean(self):
        super().clean()

        # User joins at most one team per tournament
        user_account = self.game_account.user
        tournament = self.team.tournament

        conflict = TeamMember.objects.filter(
            game_account__user_account = user_account,
            team__tournament = tournament,
        ).exclude(pk=self.pk)

        if conflict.exists():
            raise ValidationError(
                "This user is already in another team for this tournament."
            )

        # There is exactly one leader per team
        team = self.team
        leader_count = TeamMember.objects.filter(
            team = self.team,
            is_leader = True,
        ).exclude(pk=self.pk).count() + (1 if self.is_leader else 0)
        if (leader_count == 0):
            raise ValidationError("This team must have a leader.")
        elif (leader_count > 1):
            raise ValidationError("This team already has a leader.")

    def __str__(self):
        return f'{game_account} ({team}) {"leader" if is_leader else "member"}'
