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
    list_display = ('name', 'category', 'price', 'cost_price', 'profit_margin_display', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_popular', 'is_active')
    list_filter = (
        'category', 'is_popular', 'is_active', 'is_featured', 'is_seasonal',
        'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'is_nut_free',
        'is_low_carb', 'is_keto_friendly', 'spice_level'
    )
    search_fields = ('name', 'description', 'ingredients', 'allergens')
    list_editable = ('price', 'cost_price', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_popular', 'is_active')
    autocomplete_fields = ('category',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'price', 'image')
        }),
        ('Cost & Pricing', {
            'fields': ('cost_price',),
            'description': 'Used for profitability tracking and analytics.'
        }),
        ('Dietary Information', {
            'fields': (
                ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'is_nut_free'),
                ('is_low_carb', 'is_keto_friendly', 'spice_level'),
                'calories', 'protein_grams', 'carbs_grams', 'fat_grams', 'fiber_grams', 'sugar_grams', 'sodium_mg',
                'serving_size', 'ingredients', 'allergens'
            )
        }),
        ('Status', {
            'fields': ('is_popular', 'is_featured', 'is_seasonal', 'is_active')
        }),
    )

    def profit_margin_display(self, obj):
        margin = obj.get_profit_margin()
        if margin is None:
            return 'N/A'
        return f"{margin}%"
    profit_margin_display.short_description = 'Profit Margin'
