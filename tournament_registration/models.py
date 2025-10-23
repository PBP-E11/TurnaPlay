import uuid
from tournaments.models import Tournament
from game_account.models import GameAccount
from django.db import models
from django.core.exceptions import ValidationError

class TournamentRegistration(models.Model):
    """
    Model representing a registration attempt (it can be complete or in progress), or in other words team details
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

    @property
    def max_team_size(self) -> int:
        return self.tournament.tournament_format.team_size

    def __str__(self):
        return f'{self.team_name} ({self.tournament})'

class TeamMember(models.Model):
    """
    A many to one relation for members that has joined a team
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

    # Ordering
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['team', 'order'], name='unique_member_order_in_a_team')
        ]

    def clean(self):
        super().clean()

        # User joins at most one team per tournament
        user_account = self.game_account.user
        tournament = self.team.tournament

        conflict = TeamMember.objects.filter(
            game_account__user = user_account,
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

        # Cap members per team based on tournament setting
        max_members = tournament.tournament_format.team_size
        count = TeamMember.objects.filter(team=self.team).exclude(pk=self.pk).count()
        if count + 1 > max_members:
            raise ValidationError(f"Cannot have more than {max_members} members in this team.")

        # Enforce order doesn’t exceed team capacity
        if max_members is not None and self.order >= max_members:
            raise ValidationError(f"Order must be less than {max_members} for this tournament format.")

        # Make sure order 0 is only for leader
        if self.order == 0 and not is_leader:
            raise ValidationError(f"Order 0 is only for leader")

        if is_leader and self.order != 0:
            raise ValidationError(f"Leader must have order 0")

    def __str__(self):
        return f'{self.game_account} ({self.team}) {"leader" if self.is_leader else "member"}'
