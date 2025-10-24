from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import GameAccount
from tournaments.models import Game
import json
import uuid

class GameAccountTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test game
        self.game = Game.objects.create(
            name='Test Game'
        )
        
        # Create a test game account
        self.game_account = GameAccount.objects.create(
            user=self.user,
            game=self.game,
            ingame_name='TestPlayer123',
            active=True
        )
        
        # Set up the test client
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_game_account_creation(self):
        # Test that a game account can be created
        self.assertEqual(self.game_account.ingame_name, 'TestPlayer123')
        self.assertEqual(self.game_account.user, self.user)
        self.assertEqual(self.game_account.game, self.game)
        self.assertTrue(self.game_account.active)

    def test_unique_ingame_name_constraint(self):
        # Test that two active accounts cannot have the same ingame_name for the same game
        # Try to create another account with same game and ingame_name
        with self.assertRaises(Exception):
            GameAccount.objects.create(
                user=self.user,
                game=self.game,
                ingame_name='TestPlayer123',
                active=True
            )

    def test_list_game_accounts(self):
        # Test listing game accounts
        response = self.client.get(reverse('game_account:gameaccount-list-create'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['ingame_name'], 'TestPlayer123')

    def test_create_game_account(self):
        # Test creating a new game account via API
        data = {
            'game': str(self.game.id),
            'ingame_name': 'NewPlayer456',
            'active': True
        }
        response = self.client.post(
            reverse('game_account:gameaccount-list-create'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GameAccount.objects.count(), 2)

    def test_filter_by_game(self):
        # Test filtering game accounts by game
        response = self.client.get(
            f"{reverse('game_account:gameaccount-list-create')}?game={self.game.id}"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['game_id'], str(self.game.id))
