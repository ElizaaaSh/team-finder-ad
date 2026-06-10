from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="password123",
            name="Test",
            surname="User",
            phone="+79000000201",
        )

    def test_register_page_is_available(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Регистрация")

    def test_login_with_email(self):
        response = self.client.post(
            reverse("users:login"),
            {"email": "user@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("projects:list"))

    def test_profile_edit_requires_login(self):
        response = self.client.get(reverse("users:edit_profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response["Location"])

    def test_phone_is_normalized_on_profile_edit(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Test",
                "surname": "User",
                "about": "About",
                "phone": "89000000201",
                "github_url": "https://github.com/test-user",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79000000201")
