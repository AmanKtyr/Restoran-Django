from django.contrib import admin
from .models import Review, ReviewLike

class ReviewLikeInline(admin.TabularInline):
    model = ReviewLike
    extra = 0
    readonly_fields = ('user', 'created_at')
    can_delete = False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('user__username', 'menu_item__name', 'title', 'content')
    readonly_fields = ('user', 'menu_item', 'order_item', 'created_at', 'updated_at')
    list_editable = ('is_approved',)
    inlines = [ReviewLikeInline]
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'menu_item', 'order_item', 'rating', 'title', 'content', 'image')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
