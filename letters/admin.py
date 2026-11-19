from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BackgroundMusic, LetterPhoto, LetterTheme, LetterView, LoveLetter, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "display_name", "email", "is_staff", "date_joined")
    search_fields = ("username", "email", "display_name")
    fieldsets = BaseUserAdmin.fieldsets + (("Profile", {"fields": ("display_name",)}),)


class LetterPhotoInline(admin.TabularInline):
    model = LetterPhoto
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(LoveLetter)
class LoveLetterAdmin(admin.ModelAdmin):
    list_display = (
        "title", "recipient_name", "sender_name", "owner", "status",
        "is_public", "view_count", "updated_at",
    )
    list_filter = ("status", "is_public", "occasion", "theme", "created_at")
    search_fields = ("title", "recipient_name", "sender_name", "owner__username", "slug")
    prepopulated_fields = {}
    readonly_fields = ("slug", "view_count", "published_at", "created_at", "updated_at", "last_opened_at")
    inlines = [LetterPhotoInline]
    list_select_related = ("owner", "theme")
    actions = ["make_published", "make_draft"]

    @admin.action(description="Publish selected letters")
    def make_published(self, request, queryset):
        for letter in queryset:
            letter.publish()
        self.message_user(request, f"{queryset.count()} letter(s) published.")

    @admin.action(description="Move selected letters to drafts")
    def make_draft(self, request, queryset):
        queryset.update(status=LoveLetter.Status.DRAFT)
        self.message_user(request, f"{queryset.count()} letter(s) moved to drafts.")


@admin.register(LetterTheme)
class LetterThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tagline", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BackgroundMusic)
class BackgroundMusicAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "mood", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("title", "artist")


@admin.register(LetterPhoto)
class LetterPhotoAdmin(admin.ModelAdmin):
    list_display = ("letter", "caption", "order", "created_at")
    list_select_related = ("letter",)


@admin.register(LetterView)
class LetterViewAdmin(admin.ModelAdmin):
    list_display = ("letter", "viewed_at", "ip_hash")
    list_filter = ("viewed_at",)
    search_fields = ("letter__title", "letter__slug")
    readonly_fields = ("letter", "ip_hash", "user_agent", "referrer", "viewed_at")

    def has_add_permission(self, request):
        return False
