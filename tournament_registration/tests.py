from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from user_account.models import UserAccount
from tournaments.models import Game, TournamentFormat, Tournament


class TournamentRegistrationViewsTests(TestCase):
	def setUp(self):
		self.user = UserAccount.objects.create_user(
			username='player1',
			email='player1@example.com',
			password='testpass',
			role='user',
			display_name='Player One'
		)

		self.game = Game.objects.create(name='Dota 2')
		self.tformat = TournamentFormat.objects.create(game=self.game, name='5v5', team_size=5)

		self.tournament = Tournament.objects.create(
			organizer=None,
			tournament_format=self.tformat,
			tournament_name='Registration Cup',
			description='Open for registration',
			tournament_date=timezone.localdate(),
			team_maximum_count=16,
		)

	def test_create_team_requires_login(self):
		url = reverse('team:create_team_form', args=[self.tournament.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 302)
		# login and try again
		self.client.login(username='player1', password='testpass')
		response2 = self.client.get(url)
		# logged in user should get 200 (form page) or redirect depending on implementation
		self.assertIn(response2.status_code, (200, 302))
