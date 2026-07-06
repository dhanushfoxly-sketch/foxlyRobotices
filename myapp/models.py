from django.db import models
from django.conf import settings
import uuid
import zipfile
import os
from datetime import datetime
from django.core.files import File as DjangoFile
from django.utils import timezone

class BoardType(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Board Type'
        verbose_name_plural = 'Board Types'

    def __str__(self):
        return self.name


class Component(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    # Quantity is now stored per-project in ProjectComponent

    class Meta:
        verbose_name = 'Component'
        verbose_name_plural = 'Components'

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=180)
    board_type = models.ForeignKey(BoardType, on_delete=models.CASCADE, related_name='projects')
    components = models.ManyToManyField(Component, related_name='projects', blank=True, through='ProjectComponent')
    description = models.TextField()
    featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to='projects/images/', blank=True, null=True)
    zip_file = models.FileField(upload_to='projects/zips/', blank=True, null=True)
    # circuit_diagram and code_file removed; admin uploads ZIP files via the Project admin form
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.zip_file:
            return

        zip_path = self.zip_file.path
        if not os.path.exists(zip_path):
            return

        extract_dir = os.path.join(
            settings.MEDIA_ROOT,
            'projects',
            f"project_{self.id}_{os.path.splitext(os.path.basename(zip_path))[0]}"
        )
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            return

        needs_save = False

        if not self.image:
            image_path = None
            for root, dirs, files in os.walk(extract_dir):
                for fname in files:
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_path = os.path.join(root, fname)
                        break
                if image_path:
                    break
            if image_path:
                try:
                    with open(image_path, 'rb') as f:
                        django_file = DjangoFile(f)
                        self.image.save(os.path.basename(image_path), django_file, save=False)
                        needs_save = True
                except Exception:
                    pass

        if not self.description:
            description = ''
            for name in ('README.md', 'README.txt', 'readme.md', 'readme.txt'):
                candidate = os.path.join(extract_dir, name)
                if os.path.exists(candidate):
                    try:
                        with open(candidate, 'r', encoding='utf-8') as f:
                            description = f.read()
                    except Exception:
                        description = ''
                    break
            if description:
                self.description = description
                needs_save = True

        if needs_save:
            super().save(update_fields=['image', 'description'] if self.image and self.description else ['image'] if self.image else ['description'])


class DownloadRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='download_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='download_requests', blank=True, null=True)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    access_code = models.CharField(max_length=32, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    request_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Download Request'
        verbose_name_plural = 'Download Requests'

    def __str__(self):
        return f"{self.project.title} request by {self.name}"

    def contact_text(self):
        parts = []
        if self.email:
            parts.append(self.email)
        if self.phone_number:
            parts.append(self.phone_number)
        return ' / '.join(parts)


class ProjectComponent(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_components')
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('project', 'component')

    def __str__(self):
        return f"{self.component.name} (x{self.quantity})"

