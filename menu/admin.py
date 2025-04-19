from django.contrib import admin
from .models import Category, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'small_description', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'small_description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'is_active')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_popular', 'is_active')
    list_filter = (
        'category', 'is_popular', 'is_active', 'is_featured', 'is_seasonal',
        'is_vegetarian', 'is_vegan', 'is_gluten_free', 'spice_level'
    )
    search_fields = ('name', 'description', 'ingredients', 'allergens')
    list_editable = ('price', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_popular', 'is_active')
    autocomplete_fields = ('category',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'price', 'image')
        }),
        ('Dietary Information', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'spice_level', 'calories', 'ingredients', 'allergens')
        }),
        ('Status', {
            'fields': ('is_popular', 'is_featured', 'is_seasonal', 'is_active')
        }),
    )
