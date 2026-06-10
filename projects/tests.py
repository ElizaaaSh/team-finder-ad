import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Project, Skill


class ProjectViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="owner@example.com",
            password="password123",
            name="Owner",
            surname="User",
            phone="+79000000101",
        )
        self.member = user_model.objects.create_user(
            email="member@example.com",
            password="password123",
            name="Member",
            surname="User",
            phone="+79000000102",
        )
        self.skill = Skill.objects.create(name="Django")
        self.project = Project.objects.create(
            name="Test Project",
            description="Description",
            owner=self.owner,
            github_url="https://github.com/example/project",
        )
        self.project.participants.add(self.owner)
        self.project.skills.add(self.skill)

    def test_project_list_and_filter(self):
        response = self.client.get(reverse("projects:list"), {"skill": "Django"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")

    def test_guest_cannot_create_project(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response["Location"])

    def test_owner_can_add_and_remove_project_skill(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"name": "Docker"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["created"])
        self.assertTrue(payload["added"])

        response = self.client.post(
            reverse(
                "projects:remove_skill",
                kwargs={"pk": self.project.pk, "skill_id": payload["skill_id"]},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.project.skills.filter(name="Docker").exists())

    def test_authenticated_user_can_toggle_participation(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("projects:toggle_participate", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["participant"])
        self.assertTrue(self.project.participants.filter(pk=self.member.pk).exists())
