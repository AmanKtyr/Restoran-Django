# Generated by Django 5.2 on 2025-04-20 19:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_bio_userprofile_dietary_preference_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractivity',
            name='activity_type',
            field=models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('register', 'Registration'), ('profile_update', 'Profile Update'), ('password_change', 'Password Change'), ('order', 'Order Placed'), ('booking', 'Booking Made'), ('review', 'Review Posted'), ('favorite', 'Item Favorited'), ('loyalty', 'Loyalty Activity'), ('address_added', 'Address Added'), ('address_updated', 'Address Updated'), ('address_removed', 'Address Removed'), ('email_verified', 'Email Verified'), ('two_factor_enabled', 'Two-Factor Authentication Enabled'), ('two_factor_disabled', 'Two-Factor Authentication Disabled'), ('email_verification_sent', 'Email Verification Sent'), ('referral_created', 'Referral Created'), ('referral_completed', 'Referral Completed'), ('referral_bonus_earned', 'Referral Bonus Earned'), ('referral_bonus_redeemed', 'Referral Bonus Redeemed')], max_length=30),
        ),
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email Verification Token',
                'verbose_name_plural': 'Email Verification Tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReferralBonus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bonus_type', models.CharField(choices=[('points', 'Loyalty Points'), ('discount', 'Discount'), ('free_item', 'Free Item')], max_length=20)),
                ('bonus_value', models.DecimalField(decimal_places=2, help_text='Value of the bonus (points, discount amount, etc.)', max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('redeemed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('referred', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_bonuses_received', to=settings.AUTH_USER_MODEL)),
                ('referrer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_bonuses_given', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Referral Bonus',
                'verbose_name_plural': 'Referral Bonuses',
                'ordering': ['-created_at'],
            },
        ),
    ]
