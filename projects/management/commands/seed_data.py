from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import Project, Skill
from users.models import User


class Command(BaseCommand):
    help = "Creates demo users, projects and skills for TeamFinder."

    def handle(self, *args, **options):
        users_data = [
            {
                "email": "anna@example.com",
                "name": "Анна",
                "surname": "Иванова",
                "phone": "+79000000001",
                "github_url": "https://github.com/anna-teamfinder",
                "about": "Frontend-разработчик, люблю интерфейсы для pet-проектов.",
            },
            {
                "email": "pavel@example.com",
                "name": "Павел",
                "surname": "Смирнов",
                "phone": "+79000000002",
                "github_url": "https://github.com/pavel-teamfinder",
                "about": "Backend-разработчик на Django и PostgreSQL.",
            },
            {
                "email": "maria@example.com",
                "name": "Мария",
                "surname": "Петрова",
                "phone": "+79000000003",
                "github_url": "https://github.com/maria-teamfinder",
                "about": "UI/UX-дизайнер, делаю прототипы и дизайн-системы.",
            },
            {
                "email": "ivan@example.com",
                "name": "Иван",
                "surname": "Кузнецов",
                "phone": "+79000000004",
                "github_url": "https://github.com/ivan-teamfinder",
                "about": "Data science и автоматизация аналитики.",
            },
        ]

        demo_users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults=data,
            )
            if created:
                user.set_password("password123")
                user.save()
            demo_users.append(user)

        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "name": "Админ",
                "surname": "TeamFinder",
                "phone": "+79000000099",
                "is_staff": True,
                "is_superuser": True,
                "about": "Администратор проекта.",
            },
        )
        if created:
            admin.set_password("admin12345")
            admin.save()

        skill_names = [
            "Django",
            "PostgreSQL",
            "JavaScript",
            "React",
            "Docker",
            "UI/UX",
            "Python",
            "Data Science",
        ]
        skills = {name: Skill.objects.get_or_create(name=name)[0] for name in skill_names}

        projects_data = [
            {
                "owner": demo_users[3],
                "name": "Data Pets",
                "description": "Каталог открытых датасетов для маленьких ML-проектов.",
                "github_url": "https://github.com/ivan-teamfinder/data-pets",
                "skills": ["Python", "Data Science", "PostgreSQL"],
                "participants": [demo_users[1]],
                "created_at": datetime(2025, 10, 10, 12, 0),
            },
            {
                "owner": demo_users[2],
                "name": "Portfolio Match",
                "description": "Сервис для подбора дизайнеров и разработчиков по портфолио.",
                "github_url": "https://github.com/maria-teamfinder/portfolio-match",
                "skills": ["React", "UI/UX", "JavaScript"],
                "participants": [demo_users[3]],
                "created_at": datetime(2025, 10, 9, 15, 30),
            },
            {
                "owner": demo_users[1],
                "name": "TaskFlow",
                "description": "Мини-сервис для командного планирования задач pet-проектов.",
                "github_url": "https://github.com/pavel-teamfinder/taskflow",
                "skills": ["Django", "PostgreSQL", "Docker"],
                "participants": [demo_users[0]],
                "created_at": datetime(2025, 10, 9, 10, 0),
            },
            {
                "owner": demo_users[0],
                "name": "StudyBuddy",
                "description": "Платформа для поиска партнёров по подготовке к экзаменам.",
                "github_url": "https://github.com/anna-teamfinder/studybuddy",
                "skills": ["Django", "JavaScript", "UI/UX"],
                "participants": [demo_users[1], demo_users[2]],
                "created_at": datetime(2025, 10, 8, 9, 0),
            },
            {
                "owner": admin,
                "name": "Admin Demo Project",
                "description": (
                    "Служебный пример проекта администратора "
                    "для проверки прав в админ-панели."
                ),
                "github_url": "https://github.com/teamfinder/admin-demo",
                "skills": ["Django", "Docker"],
                "participants": [demo_users[0]],
                "created_at": datetime(2025, 10, 7, 9, 0),
            },
        ]

        for data in projects_data:
            project, _ = Project.objects.update_or_create(
                owner=data["owner"],
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "github_url": data["github_url"],
                    "status": Project.STATUS_OPEN,
                },
            )
            project.participants.set([data["owner"], *data["participants"]])
            project.skills.set([skills[name] for name in data["skills"]])
            Project.objects.filter(pk=project.pk).update(
                created_at=timezone.make_aware(data["created_at"])
            )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Users: anna@example.com / password123, pavel@example.com / password123")
        self.stdout.write("Admin: admin@example.com / admin12345")
