from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project, Skill

User = get_user_model()

USERS = [
    {
        "email": "admin@teamfinder.ru",
        "password": "admin1234",
        "name": "Алексей",
        "surname": "Иванов",
        "about": "Fullstack-разработчик, люблю Python и Django.",
        "phone": "+7 (900) 123-45-67",
        "github_url": "https://github.com/alexivanov",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "maria@teamfinder.ru",
        "password": "maria1234",
        "name": "Мария",
        "surname": "Петрова",
        "about": "UX/UI дизайнер с 5-летним опытом.",
        "phone": "+7 (900) 234-56-78",
        "github_url": "https://github.com/mariapetrova",
    },
    {
        "email": "dmitry@teamfinder.ru",
        "password": "dmitry1234",
        "name": "Дмитрий",
        "surname": "Сидоров",
        "about": "Backend-разработчик, специализируюсь на Go и PostgreSQL.",
        "phone": "+7 (900) 345-67-89",
        "github_url": "https://github.com/dmitrysidorov",
    },
    {
        "email": "elena@teamfinder.ru",
        "password": "elena1234",
        "name": "Елена",
        "surname": "Козлова",
        "about": "Data Scientist, увлекаюсь ML и анализом данных.",
        "phone": "+7 (900) 456-78-90",
        "github_url": "https://github.com/elenakozlova",
    },
    {
        "email": "ivan@teamfinder.ru",
        "password": "ivan1234",
        "name": "Иван",
        "surname": "Новиков",
        "about": "Mobile-разработчик (iOS/Android), Swift и Kotlin.",
        "phone": "+7 (900) 567-89-01",
        "github_url": "https://github.com/ivannovikov",
    },
]

SKILLS_DATA = [
    "Python", "Django", "React", "PostgreSQL", "Docker",
    "JavaScript", "Go", "Swift", "Machine Learning", "UI/UX Design",
]

PROJECTS = [
    {
        "owner_email": "admin@teamfinder.ru",
        "name": "TeamFinder Platform",
        "description": (
            "Платформа для поиска команды и участников проектов. "
            "Разрабатываем новые функции и улучшаем UX."
        ),
        "github_url": "https://github.com/teamfinder/platform",
        "status": "open",
        "skills": ["Python", "Django", "React", "PostgreSQL"],
        "participants": ["maria@teamfinder.ru", "dmitry@teamfinder.ru"],
    },
    {
        "owner_email": "admin@teamfinder.ru",
        "name": "Open Source CMS",
        "description": (
            "Разрабатываем open-source систему управления контентом на Django. "
            "Ищем frontend-разработчиков."
        ),
        "github_url": "https://github.com/teamfinder/cms",
        "status": "open",
        "skills": ["Python", "Django", "JavaScript"],
        "participants": ["elena@teamfinder.ru"],
    },
    {
        "owner_email": "maria@teamfinder.ru",
        "name": "Design System",
        "description": (
            "Создаём универсальную дизайн-систему для веб-приложений "
            "с набором компонентов и гайдлайнами."
        ),
        "github_url": "https://github.com/mariapetrova/design-system",
        "status": "open",
        "skills": ["UI/UX Design", "React", "JavaScript"],
        "participants": ["admin@teamfinder.ru"],
    },
    {
        "owner_email": "dmitry@teamfinder.ru",
        "name": "Microservices API Gateway",
        "description": (
            "Высоконагруженный API Gateway на Go с поддержкой "
            "балансировки нагрузки и кэширования."
        ),
        "github_url": "https://github.com/dmitrysidorov/api-gateway",
        "status": "open",
        "skills": ["Go", "PostgreSQL", "Docker"],
        "participants": ["admin@teamfinder.ru", "ivan@teamfinder.ru"],
    },
    {
        "owner_email": "elena@teamfinder.ru",
        "name": "ML Recommendation Engine",
        "description": "Движок рекомендаций на основе машинного обучения для e-commerce платформ.",
        "github_url": "https://github.com/elenakozlova/rec-engine",
        "status": "open",
        "skills": ["Machine Learning", "Python"],
        "participants": ["admin@teamfinder.ru"],
    },
    {
        "owner_email": "ivan@teamfinder.ru",
        "name": "Cross-Platform Mobile App",
        "description": (
            "Кроссплатформенное мобильное приложение для управления задачами и проектами."
        ),
        "github_url": "https://github.com/ivannovikov/taskapp",
        "status": "open",
        "skills": ["Swift", "React"],
        "participants": ["maria@teamfinder.ru"],
    },
    {
        "owner_email": "dmitry@teamfinder.ru",
        "name": "Legacy System Migration",
        "description": "Успешно завершили миграцию устаревшей системы на современный стек.",
        "github_url": "",
        "status": "closed",
        "skills": ["Python", "PostgreSQL"],
        "participants": [],
    },
]


class Command(BaseCommand):
    help = "Seed the database with test users and projects"

    def handle(self, *args, **options):
        if User.objects.filter(email="admin@teamfinder.ru").exists():
            self.stdout.write(self.style.WARNING("Seed data already exists. Skipping."))
            return

        self.stdout.write("Creating skills...")
        skills = {}
        for skill_name in SKILLS_DATA:
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            skills[skill_name] = skill

        self.stdout.write("Creating users...")
        users = {}
        for source_user_data in USERS:
            user_data = source_user_data.copy()
            is_staff = user_data.pop("is_staff", False)
            is_superuser = user_data.pop("is_superuser", False)
            password = user_data.pop("password")
            email = user_data["email"]

            user = User(**user_data)
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            users[email] = user
            self.stdout.write(f"  Created user: {email}")

        self.stdout.write("Creating projects...")
        for proj_data in PROJECTS:
            owner = users[proj_data["owner_email"]]
            project = Project.objects.create(
                name=proj_data["name"],
                description=proj_data["description"],
                github_url=proj_data.get("github_url", ""),
                status=proj_data["status"],
                owner=owner,
            )
            for skill_name in proj_data.get("skills", []):
                if skill_name in skills:
                    project.skills.add(skills[skill_name])
            for participant_email in proj_data.get("participants", []):
                if participant_email in users:
                    project.participants.add(users[participant_email])
            self.stdout.write(f"  Created project: {project.name}")

        self.stdout.write(self.style.SUCCESS("Seed data created successfully!"))
        self.stdout.write(self.style.SUCCESS("Admin login: admin@teamfinder.ru / admin1234"))
