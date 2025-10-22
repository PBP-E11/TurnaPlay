from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid

class UserAccountManager(BaseUserManager):
    """
    Manager khusus untuk UserAccount.
    
    Manager ini menangani pembuatan user dan superuser.
    Django memerlukan create_user() dan create_superuser() untuk autentikasi.
    """
    
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Membuat dan menyimpan User biasa.
        
        Args:
            username: Username untuk login
            email: Email user
            password: Password plain text (akan di-hash otomatis)
            **extra_fields: Field tambahan seperti display_name, role
            
        Returns:
            UserAccount object yang sudah tersimpan
        """
        if not username:
            raise ValueError('Username harus diisi')
        if not email:
            raise ValueError('Email harus diisi')
        
        # Normalize email (lowercase domain part)
        email = self.normalize_email(email)
        
        # Set default display_name jika tidak ada
        if 'display_name' not in extra_fields:
            extra_fields['display_name'] = username
        
        # Set role default ke 'user' jika tidak dispesifikasi
        if 'role' not in extra_fields:
            extra_fields['role'] = 'user'
        
        # Buat instance user
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        
        # set_password akan otomatis hash password
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Membuat dan menyimpan Superuser (Admin).
        
        Dipanggil oleh command 'python manage.py createsuperuser'
        """
        # Set role ke admin
        extra_fields['role'] = 'admin'
        
        # Buat user dengan method create_user
        user = self.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )
        
        return user

class UserAccount(AbstractBaseUser, PermissionsMixin):
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
    username = models.CharField(max_length=60, unique=True)
    
    # Email - untuk login alternatif dan komunikasi
    email = models.EmailField(max_length=254, unique=True)
    
    # Display Name - nama yang ditampilkan ke publik
    display_name = models.CharField(max_length=255)
    
    # Role - menentukan hak akses pengguna
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    # Active - untuk soft delete (tidak benar-benar hapus dari database)
    # False = akun dinonaktifkan/dihapus
    # required oleh django auth
    is_active = models.BooleanField(default=True)

    # Timestamp
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserAccountManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        """
        Meta options untuk model UserAccount.
        
        Constraints:
        - Username dan email hanya harus unik untuk akun yang aktif
        - Ini memungkinkan username/email yang sama digunakan lagi 
          setelah akun dihapus (inactive)
        """
        # Ordering default saat query
        ordering = ['-date_joined'] 
        
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
    
    @property
    def is_staff(self):
        """
        Property required oleh Django Admin.
        
        Django Admin mengecek is_staff untuk menentukan siapa yang boleh
        akses admin panel di /admin/.
        
        Hanya user dengan role='admin' yang bisa akses Django Admin.
        
        Returns:
            bool: True jika role adalah 'admin'
        """
        return self.role == 'admin'
    
    def has_perm(self, perm, obj=None):
        """
        Required oleh Django Admin untuk permission checking.
        
        Admin memiliki semua permission.
        
        Args:
            perm: Permission string (e.g., 'app.add_model')
            obj: Optional object untuk object-level permission
            
        Returns:
            bool: True jika user adalah admin
        """
        return self.is_admin()
    
    def has_module_perms(self, app_label):
        """
        Required oleh Django Admin untuk module-level permission.
        
        Admin bisa akses semua module/app.
        
        Args:
            app_label: Nama app (e.g., 'tournament', 'user_account')
            
        Returns:
            bool: True jika user adalah admin
        """
        return self.is_admin()
