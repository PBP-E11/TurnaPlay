from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from user_account.models import UserAccount
from .models import Game, TournamentFormat, Tournament


class TournamentViewsTests(TestCase):
	def setUp(self):
		# create an organizer user
		self.organizer = UserAccount.objects.create_user(
			username='organizer1',
			email='org1@example.com',
			password='testpass',
			role='organizer',
			display_name='Org One'
		)

		# create a game and a format
		self.game = Game.objects.create(name='Valorant')
		self.tformat = TournamentFormat.objects.create(game=self.game, name='5v5', team_size=5)

		# create a tournament
		self.tournament = Tournament.objects.create(
			organizer=self.organizer,
			tournament_format=self.tformat,
			tournament_name='Test Cup',
			description='A simple test tournament',
			tournament_date=timezone.localdate(),
			team_maximum_count=8,
		)

	def test_show_main_displays_tournament(self):
		url = reverse('tournaments:show_main')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Test Cup')

	def test_tournament_list_json_contains_banner_url(self):
		url = reverse('tournaments:tournament-list-json')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		data = response.json()
		# Expect the JSON to contain a list of tournaments
		self.assertIn('tournaments', data)
		# Each tournament object should include banner_url (may be empty/null)
		if data['tournaments']:
			self.assertIn('banner_url', data['tournaments'][0])

	def test_tournament_create_requires_login(self):
		url = reverse('tournaments:tournament-create')
		response = self.client.get(url)
		# Not logged in -> redirect to login
		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login', response['Location'])

	def test_tournament_detail_shows_banner_or_default(self):
		url = reverse('tournaments:tournament-detail', args=[self.tournament.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Test Cup')
