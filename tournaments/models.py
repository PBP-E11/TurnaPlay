import uuid
from django.db import models
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from user_account.models import UserAccount

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
    
    Relationships:
    - One-to-Many with UserAccount (organizer): One organizer can create many tournaments
    - Many-to-Many with UserAccount (participants): Through TournamentParticipant model
    """
    # PK ID (UUID4)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Organizer (user who created the tournament)
    organizer = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE, 
        related_name='organized_tournaments',
        verbose_name=_("Organizer"),
        limit_choices_to={'role__in': ['organizer', 'admin']},
        null=True,
        blank=True,
    )
    objects = TournamentManager()  # Custom manager that annotates is_active
    

    # FK tournament_format.id
    tournament_format = models.ForeignKey(
        TournamentFormat,
        on_delete=models.PROTECT,
        related_name='tournaments',
        verbose_name=_("Tournament Format")
    )

    # Through model allows additional fields like registration date, status, etc.
    participants = models.ManyToManyField(
        UserAccount,
        through='TournamentParticipant',
        related_name='participated_tournaments',
        verbose_name=_("Participants")
    )

    # Tournament Details
    tournament_name = models.CharField(max_length=255, verbose_name=_("Tournament Name"))
    description = models.TextField(verbose_name=_("Description"))
    
    # Date
    tournament_date = models.DateField(verbose_name=_("Tournament Date"), null=True, blank=True)    
    
    # Financials
    prize_pool = models.PositiveIntegerField(default=0, verbose_name=_("Prize Pool (IDR)"))
    
    # Media
    banner = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("Banner Image URL"))

    # Team Counts
    team_maximum_count = models.PositiveIntegerField(verbose_name=_("Maximum Team Entry"))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Tournament")
        verbose_name_plural = _("Tournaments")
        ordering = ['-created_at', 'tournament_date', 'tournament_name']

    def __str__(self):
        return self.tournament_name

    def clean(self):
        """
        Custom validation to enforce constraints.
        """
        super().clean()

        # Maximum team count must be at least 1
        if self.team_maximum_count < 1:
            raise ValidationError(
                {'team_maximum_count': _('A tournament must allow at least one team.')}
            )
        
        # Prevent past tournament dates
        if self.tournament_date and self.tournament_date < timezone.localdate():
            raise ValidationError(
                {'tournament_date': _('Tournament date cannot be in the past.')}
            )

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this tournament."""
        return reverse('tournament-detail', args=[str(self.id)])

    def participants_count(self):
        """Returns the current number of registered participants."""
        return self.participants.count()

    @property
    def status(self):
        if self.tournament_date and self.tournament_date < timezone.localdate():
            return "selesai"
        return "ongoing"


class TournamentParticipant(models.Model):
    """
    Through model for Many-to-Many relationship between Tournament and UserAccount.
    Stores additional information about tournament participation.
    
    Relationships:
    - Many-to-One with Tournament: Many participants per tournament
    - Many-to-One with UserAccount: One user can participate in many tournaments
    """
    
    STATUS_CHOICES = [
        ('registered', _('Registered')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('disqualified', _('Disqualified')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # FK to Tournament
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,  # Delete participation when tournament is deleted
        related_name='participant_records',
        verbose_name=_("Tournament")
    )
    
    # FK to UserAccount
    participant = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,  # Delete participation when user is deleted
        related_name='tournament_participations',
        verbose_name=_("Participant"),
        limit_choices_to={'role': 'user'}  # Only regular users can participate
    )
    
    # Participation Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered',
        verbose_name=_("Status")
    )
    
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Registration Date"))
    
    # Optional: Team information (if applicable)
    team_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Team Name")
    )
    
    class Meta:
        verbose_name = _("Tournament Participant")
        verbose_name_plural = _("Tournament Participants")
        # Ensure one user can only register once per tournament
        unique_together = ('tournament', 'participant')
        ordering = ['registered_at']
    
    def __str__(self):
        return f"{self.participant.username} - {self.tournament.tournament_name}"
    
    def clean(self):
        """
        Validate participation constraints.
        """
        super().clean()
        
        # Check if tournament is full
        if self.tournament.is_full and not self.pk:  # Only check for new registrations
            raise ValidationError(
                _('This tournament has reached maximum participants.')
            )
        
        # Validate participant role
        if self.participant and not self.participant.role == 'user':
            raise ValidationError(
                {'participant': _('Only users with "user" role can participate in tournaments.')}
            )