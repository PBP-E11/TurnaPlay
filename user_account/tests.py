from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import UserAccount, UserAccountManager
from .forms import (
    LoginForm, RegisterForm, ProfileUpdateForm, CreateOrganizerForm
)
from tournaments.models import Tournament, TournamentFormat, Game
from tournament_registration.models import TournamentRegistration
from datetime import date, timedelta
import uuid

User = get_user_model()


# ==================== MODEL TESTS ====================

class UserAccountManagerTests(TestCase):
    """Test UserAccountManager methods"""
    
    def test_create_user_success(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'user')
        self.assertEqual(user.display_name, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
    
    def test_create_user_with_extra_fields(self):
        """Test creating user with extra fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            display_name='Test User',
            role='organizer'
        )
        self.assertEqual(user.display_name, 'Test User')
        self.assertEqual(user.role, 'organizer')
    
    def test_create_user_without_username(self):
        """Test creating user without username raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='',
                email='test@example.com',
                password='testpass123'
            )
    
    def test_create_user_without_email(self):
        """Test creating user without email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='testuser',
                email='',
                password='testpass123'
            )
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_admin())
        self.assertTrue(user.is_staff)
    
    def test_email_normalization(self):
        """Test email is normalized"""
        user = User.objects.create_user(
            username='testuser',
            email='test@EXAMPLE.COM',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')


class UserAccountModelTests(TestCase):
    """Test UserAccount model methods and properties"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='orgpass123',
            role='organizer'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def test_str_method(self):
        """Test string representation"""
        expected = f"{self.user.display_name} (@{self.user.username})"
        self.assertEqual(str(self.user), expected)
    
    def test_soft_delete(self):
        """Test soft delete sets is_active to False"""
        self.assertTrue(self.user.is_active)
        self.user.soft_delete()
        self.assertFalse(self.user.is_active)
    
    def test_is_admin_method(self):
        """Test is_admin method"""
        self.assertFalse(self.user.is_admin())
        self.assertFalse(self.organizer.is_admin())
        self.assertTrue(self.admin.is_admin())
    
    def test_is_organizer_method(self):
        """Test is_organizer method"""
        self.assertFalse(self.user.is_organizer())
        self.assertTrue(self.organizer.is_organizer())
        self.assertFalse(self.admin.is_organizer())
    
    def test_is_staff_property(self):
        """Test is_staff property"""
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.organizer.is_staff)
        self.assertTrue(self.admin.is_staff)
    
    def test_has_perm(self):
        """Test has_perm method"""
        self.assertFalse(self.user.has_perm('any_permission'))
        self.assertTrue(self.admin.has_perm('any_permission'))
    
    def test_has_module_perms(self):
        """Test has_module_perms method"""
        self.assertFalse(self.user.has_module_perms('user_account'))
        self.assertTrue(self.admin.has_module_perms('user_account'))
    
    def test_uuid_primary_key(self):
        """Test UUID is used as primary key"""
        self.assertIsInstance(self.user.id, uuid.UUID)


# ==================== FORM TESTS ====================

class LoginFormTests(TestCase):
    """Test LoginForm validation"""
    
    def test_valid_login_form(self):
        """Test valid login form"""
        form_data = {
            'username_or_email': 'testuser',
            'password': 'testpass123',
            'remember_me': True
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_without_remember_me(self):
        """Test login form without remember_me"""
        form_data = {
            'username_or_email': 'testuser',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())


class RegisterFormTests(TestCase):
    """Test RegisterForm validation"""
    
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='existpass123'
        )
    
    def test_valid_register_form(self):
        """Test valid registration form"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_duplicate_username(self):
        """Test duplicate username validation"""
        form_data = {
            'username': 'existing',
            'email': 'different@example.com',
            'display_name': 'Different User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Username already exists', str(form.errors))
    
    def test_duplicate_email(self):
        """Test duplicate email validation"""
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'display_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Email already registered', str(form.errors))
    
    def test_password_mismatch(self):
        """Test password mismatch validation"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'differentpass'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Passwords do not match', str(form.errors))
    
    def test_register_form_save(self):
        """Test form saves user with hashed password"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'display_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password('newpass123'))
        self.assertEqual(user.username, 'newuser')


class ProfileUpdateFormTests(TestCase):
    """Test ProfileUpdateForm validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
    
    def test_valid_profile_update(self):
        """Test valid profile update"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'newemail@example.com',
            'profile_image': 'avatar2'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_update_email_to_existing(self):
        """Test updating to existing email fails"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'other@example.com',
            'profile_image': 'avatar1'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Email already registered', str(form.errors))
    
    def test_password_change_without_current(self):
        """Test password change without current password fails"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'test@example.com',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Current password is required', str(form.errors))
    
    def test_password_change_with_wrong_current(self):
        """Test password change with wrong current password fails"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'test@example.com',
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Current password is incorrect', str(form.errors))
    
    def test_password_change_mismatch(self):
        """Test new password mismatch fails"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'test@example.com',
            'profile_image' : 'avatar2',
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'differentpass'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('New passwords do not match', str(form.errors))
    
    def test_successful_password_change(self):
        """Test successful password change"""
        form_data = {
            'display_name': 'Updated Name',
            'email': 'test@example.com',
			'profile_image' : 'avatar2',
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password('newpass123'))


class CreateOrganizerFormTests(TestCase):
    """Test CreateOrganizerForm validation"""
    
    def test_valid_organizer_form(self):
        """Test valid organizer creation form"""
        form_data = {
            'username': 'neworganizer',
            'email': 'organizer@example.com',
            'display_name': 'Organizer Name',
            'password': 'orgpass123',
            'password_confirm': 'orgpass123'
        }
        form = CreateOrganizerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_organizer_form_sets_role(self):
        """Test form sets role to organizer"""
        form_data = {
            'username': 'neworganizer',
            'email': 'organizer@example.com',
            'display_name': 'Organizer Name',
            'password': 'orgpass123',
            'password_confirm': 'orgpass123'
        }
        form = CreateOrganizerForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.role, 'organizer')


# ==================== VIEW TESTS ====================

class AuthenticationViewTests(TestCase):
    """Test authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('user_account:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_view_post_success(self):
        """Test successful login"""
        response = self.client.post(reverse('user_account:login'), {
            'username_or_email': 'testuser',
            'password': 'testpass123',
            'remember_me': False
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_with_email(self):
        """Test login with email"""
        response = self.client.post(reverse('user_account:login'), {
            'username_or_email': 'test@example.com',
            'password': 'testpass123',
            'remember_me': False
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_post_invalid(self):
        """Test failed login"""
        response = self.client.post(reverse('user_account:login'), {
            'username_or_email': 'testuser',
            'password': 'wrongpassword',
            'remember_me': False
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get(reverse('user_account:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
    
    def test_register_view_post_success(self):
        """Test successful registration"""
        response = self.client.post(reverse('user_account:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_logout_view(self):
        """Test logout"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_account:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_complete_profile_view_get(self):
        """Test complete profile view GET"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_account:complete_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'complete_profile.html')
    
    def test_complete_profile_view_post(self):
        """Test complete profile view POST"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('user_account:complete_profile'), {
            'profile_image': 'avatar2'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_image, 'avatar2')


class ProfileViewTests(TestCase):
    """Test profile views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_profile_view_requires_login(self):
        """Test profile view requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('user_account:profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_view_get(self):
        """Test profile view GET"""
        response = self.client.get(reverse('user_account:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
    
    def test_update_profile_view_get(self):
        """Test update profile view GET"""
        response = self.client.get(reverse('user_account:update_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_profile.html')
    
    def test_update_profile_view_post(self):
        """Test update profile view POST"""
        response = self.client.post(reverse('user_account:update_profile'), {
            'display_name': 'Updated Name',
            'email': 'updated@example.com',
            'profile_image': 'avatar3'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, 'Updated Name')
    
    def test_delete_account_view(self):
        """Test delete account view"""
        response = self.client.post(reverse('user_account:delete_account'))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class AdminDashboardTests(TestCase):
    """Test admin dashboard views"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='orgpass123',
            role='organizer'
        )
    
    def test_admin_dashboard_requires_admin(self):
        """Test admin dashboard requires admin role"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_account:admin_dashboard'))
        self.assertEqual(response.status_code, 403)
    
    def test_admin_dashboard_redirects(self):
        """Test admin dashboard redirects to manage users"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_account:admin_manage_users'))
    
    def test_admin_manage_users_view(self):
        """Test admin manage users view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_users.html')
    
    def test_admin_manage_users_search(self):
        """Test admin manage users with search"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_manage_users'), {'search': 'testuser'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
    
    def test_admin_manage_users_role_filter(self):
        """Test admin manage users with role filter"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_manage_users'), {'role': 'organizer'})
        self.assertEqual(response.status_code, 200)
    
    def test_admin_create_organizer_get(self):
        """Test admin create organizer GET"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_create_organizer'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/create_organizer.html')
    
    def test_admin_create_organizer_post(self):
        """Test admin create organizer POST"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('user_account:admin_create_organizer'), {
            'username': 'neworg',
            'email': 'neworg@example.com',
            'display_name': 'New Organizer',
            'password': 'orgpass123',
            'password_confirm': 'orgpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='neworg', role='organizer').exists())
    
    def test_admin_user_detail_view(self):
        """Test admin user detail view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_account:admin_user_detail', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/user_detail.html')
    
    def test_admin_delete_user(self):
        """Test admin delete user"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('user_account:admin_delete_user', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
    
    def test_admin_cannot_delete_self(self):
        """Test admin cannot delete their own account"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('user_account:admin_delete_user', args=[self.admin.id]))
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
    
    def test_admin_delete_nonexistent_user(self):
        """Test admin delete nonexistent user"""
        self.client.login(username='admin', password='adminpass123')
        fake_uuid = uuid.uuid4()
        response = self.client.post(reverse('user_account:admin_delete_user', args=[fake_uuid]))
        self.assertEqual(response.status_code, 404)


class AdminTournamentViewTests(TestCase):
    """Test admin tournament management views"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(username='admin', password='adminpass123')
    
    def test_admin_manage_tournaments_view(self):
        """Test admin manage tournaments view"""
        response = self.client.get(reverse('user_account:admin_manage_tournaments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tournaments.html')
    
    def test_admin_manage_tournaments_search(self):
        """Test admin manage tournaments with search"""
        response = self.client.get(reverse('user_account:admin_manage_tournaments'), {'search': 'test'})
        self.assertEqual(response.status_code, 200)


class RedirectAuthenticatedUserTests(TestCase):
    """Test redirects for authenticated users"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_view_redirects_authenticated_user(self):
        """Test login view redirects authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_account:login'))
        self.assertEqual(response.status_code, 302)
    
    def test_register_view_redirects_authenticated_user(self):
        """Test register view redirects authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_account:register'))
        self.assertEqual(response.status_code, 302)