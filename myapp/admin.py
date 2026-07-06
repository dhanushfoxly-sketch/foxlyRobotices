from django.contrib import admin
from .models import BoardType, Component, Project, ProjectComponent, DownloadRequest


@admin.register(BoardType)
class BoardTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'board_type', 'featured', 'zip_file', 'created_at')
    list_filter = ('board_type', 'featured')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    inlines = []


class ProjectComponentInline(admin.TabularInline):
    model = ProjectComponent
    extra = 1


# attach inline to ProjectAdmin
ProjectAdmin.inlines = [ProjectComponentInline]


@admin.register(DownloadRequest)
class DownloadRequestAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'name', 'email', 'phone_number', 'is_approved', 'is_used', 'created_at', 'approved_at')
    list_filter = ('is_approved', 'is_used', 'project')
    search_fields = ('user__username', 'name', 'email', 'phone_number', 'project__title', 'access_code')
    readonly_fields = ('created_at', 'approved_at')
    fieldsets = (
        (None, {
            'fields': ('project', 'user', 'name', 'email', 'phone_number', 'message', 'access_code', 'is_approved', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'approved_at')
        }),
    )


# ProjectUpload removed; uploads now create Projects directly via upload view
