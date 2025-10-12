import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class Game(models.Model):
    """
    Static model representing a playable game (e.g., Dota 2, Valorant).
    This model is used to categorize tournaments and game accounts (later).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Game Name"))
    
    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")

    def __str__(self):
        return self.name


class TournamentFormat(models.Model):
    """
    Defines the structure and team size constraints of a tournament format.
    (e.g., 5v5 Single Elimination for League of Legends)
    This is static data managed by Fahri.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # FK to the Game model
    game = models.ForeignKey(
        Game,
        on_delete=models.PROTECT,
        related_name='formats',
        verbose_name=_("Associated Game")
    )
    
    name = models.CharField(max_length=100, verbose_name=_("Format Name")) # e.g., "5v5 Draft Pick"
    team_size = models.PositiveSmallIntegerField(verbose_name=_("Players per Team")) # From user's plan
    description = models.TextField(blank=True, verbose_name=_("Format Description"))

    class Meta:
        verbose_name = _("Tournament Format")
        verbose_name_plural = _("Tournament Formats")
        # Constraint: The format name must be unique for a specific game.
        unique_together = ('game', 'name') 

    def __str__(self):
        return f"{self.name} ({self.game.name}, {self.team_size} players)"


# --- PRIMARY TOURNAMENT MODEL ---
class Tournament(models.Model):
    """
    Model representing a competitive tournament or competition.
    This module is managed by Falah.
    """
    # PK ID (UUID4)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK tournament_format.id
    tournament_format = models.ForeignKey(
        TournamentFormat,
        on_delete=models.PROTECT, # Prevents deleting a format if tournaments still use it
        related_name='tournaments',
        verbose_name=_("Tournament Format")
    )

    # Tournament Details
    tournament_name = models.CharField(max_length=255, verbose_name=_("Tournament Name"))
    description = models.TextField(verbose_name=_("Description"))
    
    # Dates
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    
    # Financials
    prize_pool = models.PositiveIntegerField(default=0, verbose_name=_("Prize Pool (IDR)")) # Constraint: prize >= 0 enforced by PositiveIntegerField
    
    # Media
    banner = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("Banner Image URL"))

    # Team Counts
    # team_count will be managed programmatically (or via a separate registration model)
    team_count = models.PositiveIntegerField(default=0, verbose_name=_("Current Team Count"))
    team_maximum_count = models.PositiveIntegerField(verbose_name=_("Maximum Team Capacity")) # Constraint: team_maximum_count > 0 enforced by PositiveIntegerField

    class Meta:
        verbose_name = _("Tournament")
        verbose_name_plural = _("Tournaments")
        # Standard ordering for display
        ordering = ['start_date', 'tournament_name']


    def __str__(self):
        return self.tournament_name

    def clean(self):
        """
        Custom validation to enforce constraints that rely on multiple fields.
        Constraints:
        1. start_date < end_date
        2. team_count <= team_maximum_count
        3. team_maximum_count > 0 (handled by PositiveIntegerField, but checked for safety)
        4. team_count >= 0 (handled by PositiveIntegerField)
        """
        super().clean()

        # 1. Start Date must be before End Date
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(
                {'end_date': _('The tournament end date must be after the start date.')}
            )

        # 2. Current teams cannot exceed maximum capacity
        if self.team_count > self.team_maximum_count:
            raise ValidationError(
                {'team_count': _('Current team count cannot exceed the maximum team capacity.')}
            )

        # 3. Maximum team count must be at least 1 for a valid tournament (although PositiveIntegerField ensures > 0)
        if self.team_maximum_count < 1:
            raise ValidationError(
                {'team_maximum_count': _('A tournament must allow at least one team.')}
            )
            
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this tournament."""
        return reverse('tournament-detail', args=[str(self.id)])
