from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название проекта"}),
            "description": forms.Textarea(attrs={"placeholder": "Описание проекта", "rows": 5}),
            "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/..."}),
            "status": forms.Select(),
        }
        labels = {
            "name": "Название",
            "description": "Описание",
            "github_url": "Репозиторий на GitHub",
            "status": "Статус",
        }
