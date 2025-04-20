from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon_class = models.CharField(max_length=50, help_text="Font Awesome class (e.g., 'fa-coffee')")
    small_description = models.CharField(max_length=100, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    SPICE_LEVEL_CHOICES = (
        (0, 'Not Spicy'),
        (1, 'Mild'),
        (2, 'Medium'),
        (3, 'Hot'),
        (4, 'Very Hot'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Cost price for profitability tracking")
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)

    # Dietary information
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    is_nut_free = models.BooleanField(default=False)
    is_low_carb = models.BooleanField(default=False)
    is_keto_friendly = models.BooleanField(default=False)
    spice_level = models.IntegerField(choices=SPICE_LEVEL_CHOICES, default=0)

    # Nutritional information
    calories = models.PositiveIntegerField(blank=True, null=True, help_text="Calories per serving")
    protein_grams = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Protein in grams")
    carbs_grams = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Carbohydrates in grams")
    fat_grams = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Fat in grams")
    fiber_grams = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Fiber in grams")
    sugar_grams = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Sugar in grams")
    sodium_mg = models.PositiveIntegerField(blank=True, null=True, help_text="Sodium in milligrams")
    serving_size = models.CharField(max_length=100, blank=True, help_text="Serving size description")

    # Ingredients and allergens
    ingredients = models.TextField(blank=True, help_text="List of ingredients")
    allergens = models.TextField(blank=True, help_text="List of allergens")

    # Status flags
    is_popular = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_seasonal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.price}"

    def get_dietary_tags(self):
        """Return a list of dietary tags for this menu item"""
        tags = []
        if self.is_vegetarian:
            tags.append('Vegetarian')
        if self.is_vegan:
            tags.append('Vegan')
        if self.is_gluten_free:
            tags.append('Gluten-Free')
        if self.is_dairy_free:
            tags.append('Dairy-Free')
        if self.is_nut_free:
            tags.append('Nut-Free')
        if self.is_low_carb:
            tags.append('Low-Carb')
        if self.is_keto_friendly:
            tags.append('Keto-Friendly')
        if self.spice_level > 0:
            tags.append(f"{self.get_spice_level_display()} Spicy")
        return tags

    def get_nutritional_info(self):
        """Return a dictionary of nutritional information"""
        return {
            'calories': self.calories,
            'protein': self.protein_grams,
            'carbs': self.carbs_grams,
            'fat': self.fat_grams,
            'fiber': self.fiber_grams,
            'sugar': self.sugar_grams,
            'sodium': self.sodium_mg,
            'serving_size': self.serving_size
        }

    def get_profit_margin(self):
        """Calculate the profit margin percentage"""
        if not self.cost_price or self.cost_price <= 0:
            return None

        profit = self.price - self.cost_price
        margin = (profit / self.price) * 100
        return round(margin, 2)
