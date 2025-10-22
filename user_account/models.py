from django.db import models
import uuid

class UserAccount(models.Model):
    """
    Model untuk menyimpan data akun pengguna TurnaPlay.
    
    Model ini menangani autentikasi dan informasi profil pengguna.
    Setiap user memiliki role yang menentukan aksesnya (user/organizer/admin).
    
    Constraints:
        - Username harus unik di antara akun yang aktif
        - Email harus unik di antara akun yang aktif
        - Akun yang inactive tidak terkena constraint unique
    
    Related Models:
        - GameAccount: One UserAccount to Many GameAccount (FK di GameAccount)
        - TournamentInvite: One UserAccount to Many TournamentInvite (FK di TournamentInvite)

    """
    
    # Role choices untuk field role
    ROLE_CHOICES = [
        ('user', 'User'),           # Pengguna biasa yang ikut turnamen
        ('organizer', 'Organizer'), # Penyelenggara turnamen
        ('admin', 'Admin'),         # Administrator sistem
    ]
    
    # Primary Key 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Username - untuk login dan mention di sistem
    # NOTE: Tidak menggunakan unique=True langsung karena ada constraint khusus
    username = models.CharField(max_length=60)
    
    # Email - untuk login alternatif dan komunikasi
    email = models.EmailField(max_length=254)
    
    # Password Hash - menyimpan hash password, bukan plain text
    password_hash = models.CharField(max_length=255)
    
    # Display Name - nama yang ditampilkan ke publik
    display_name = models.CharField(max_length=255)
    
    # Role - menentukan hak akses pengguna
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    # Active - untuk soft delete (tidak benar-benar hapus dari database)
    # False = akun dinonaktifkan/dihapus
    active = models.BooleanField(default=True)
    
    class Meta:
        """
        Meta options untuk model UserAccount.
        
        Constraints:
        - Username dan email hanya harus unik untuk akun yang aktif
        - Ini memungkinkan username/email yang sama digunakan lagi 
          setelah akun dihapus (inactive)
        """
        constraints = [
            # Constraint: Username harus unik hanya jika akun aktif
            # Contoh: user 'john' bisa dihapus (active=False), 
            # lalu username 'john' bisa dipakai user baru
            models.UniqueConstraint(
                fields=['username'],
                condition=models.Q(active=True),
                name='unique_active_username'
            ),
            # Constraint: Email harus unik hanya jika akun aktif
            models.UniqueConstraint(
                fields=['email'],
                condition=models.Q(active=True),
                name='unique_active_email'
            )
        ]
        
        # Ordering default saat query
        ordering = ['-id']  # Terbaru dulu
        
        # Nama model di Django Admin
        verbose_name = 'User Account'
        verbose_name_plural = 'User Accounts'
    
    def __str__(self):
        """
        String representation untuk model ini.
        Ditampilkan di Django Admin dan saat print().
        
        Returns:
            str: Format "Display Name (@username)"
        """
        return f"{self.display_name} (@{self.username})"
    
    def soft_delete(self):
        """
        Soft delete user account (set active=False).
        Tidak menghapus data dari database, hanya menandai sebagai inactive.
        
        Usage:
            user = UserAccount.objects.get(username='john')
            user.soft_delete()
        """
        self.active = False
        self.save()
    
    def is_admin(self):
        """
        Check apakah user adalah admin.
        
        Returns:
            bool: True jika role adalah 'admin'
        """
        return self.role == 'admin'
    
    def is_organizer(self):
        """
        Check apakah user adalah organizer.
        
        Returns:
            bool: True jika role adalah 'organizer'
        """
        return self.role == 'organizer'