import uuid
from django.db import models
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

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

    class Meta:
        verbose_name = _("Tournament Format")
        verbose_name_plural = _("Tournament Formats")
        # Constraint: The format name must be unique for a specific game.
        unique_together = ('game', 'name') 

    def __str__(self):
        return f"{self.name} ({self.game.name}, {self.team_size} players)"

class TournamentManager(models.Manager):
    """
    Custom manager for the Tournament model that dynamically annotates
    the 'is_active' status.
    """
    def get_queryset(self):
        today = timezone.localdate()
        
        # Annotate a new field 'is_active' to every query.
        # This field is True if the tournament_date is today or in the past,
        # and False if it's in the future or null.
        return super().get_queryset().annotate(
            is_active=ExpressionWrapper(
                Q(tournament_date__isnull=False) & Q(tournament_date__gte=today),
                output_field=BooleanField()
            )
        )
    
# --- PRIMARY TOURNAMENT MODEL ---
class Tournament(models.Model):
    """
    Model representing a competitive tournament or competition.
    """
    # PK ID (UUID4)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    objects = TournamentManager()  # Tell Tournament to use our new manager

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
    
    # Date
    tournament_date = models.DateField(verbose_name=_("Tournament Date"), null=True, blank=True)    
    # Financials
    prize_pool = models.PositiveIntegerField(default=0, verbose_name=_("Prize Pool (IDR)")) # Constraint: prize >= 0 enforced by PositiveIntegerField
    
    # Media
    banner = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("Banner Image URL"))

    # Team Counts
    # team_count will be managed programmatically (or via a separate registration model)
    # team_count = models.PositiveIntegerField(default=0, verbose_name=_("Current Team Count"))
    team_maximum_count = models.PositiveIntegerField(verbose_name=_("Maximum Team Entry")) # Constraint: team_maximum_count > 0 enforced by clean and PositiveIntegerField

    class Meta:
        verbose_name = _("Tournament")
        verbose_name_plural = _("Tournaments")
        # Standard ordering for display
        ordering = ['tournament_date', 'tournament_name']


    def __str__(self):
        return self.tournament_name

    def clean(self):
        """
        Custom validation to enforce constraints that rely on multiple fields.
        Constraints:
        team_maximum_count > 0 (handled by PositiveIntegerField, but checked for safety)
        """
        super().clean()

        # 2. Maximum team count must be at least 1 for a valid tournament (although PositiveIntegerField ensures > 0)
        if self.team_maximum_count < 1:
            raise ValidationError(
                {'team_maximum_count': _('A tournament must allow at least one team.')}
            )
        
                # prevent past tournament dates
        if self.tournament_date and self.tournament_date < timezone.localdate():
            raise ValidationError({'tournament_date': _('Tournament date cannot be in the past.')})
            
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this tournament."""
        return reverse('tournament-detail', args=[str(self.id)])
