import uuid
from django.db import models

class TournamentInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_account = models.ForeignKey(
        'user_account.UserAccount',
        on_delete=models.CASCADE,
        related_name='incoming_invites',
    )

    tournament_registration = models.ForeignKey(
        'tournament_registration.TournamentRegistration',
        on_delete=models.CASCADE,
        related_name='invites',
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_account', 'tournament_registration'],
                condition=models.Q(status='pending'),
                name='unique_pending_invite',
            ),
        ]

    def __str__(self):
        return f"{self.user_account} → {self.tournament_registration} ({self.status})"