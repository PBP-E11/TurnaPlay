from django.test import TestCase
from django.urls import reverse


class UserAccountTests(TestCase):
	def test_register_view_get(self):
		url = reverse('user_account:register')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

