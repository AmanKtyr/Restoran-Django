from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import datetime

from .models import EmailVerificationToken, ReferralBonus, UserActivity


def send_email_template(subject, template_name, context, recipient_list, from_email=None):
    """
    Send an email using a template.
    
    Args:
        subject: Email subject
        template_name: Path to the email template (without extension)
        context: Context data for the template
        recipient_list: List of recipient email addresses
        from_email: Sender email address (defaults to DEFAULT_FROM_EMAIL)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # Render HTML content
    html_content = render_to_string(f'emails/{template_name}.html', context)
    
    # Create plain text content
    text_content = strip_tags(html_content)
    
    # Create email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list
    )
    
    # Attach HTML content
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Send email
        email.send()
        return True
    except Exception as e:
        # Log error
        print(f"Error sending email: {e}")
        return False


def send_verification_email(user, request=None):
    """
    Send an email verification email to a user.
    
    Args:
        user: User object
        request: HTTP request object (for building absolute URLs)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Generate verification token
    token_obj = EmailVerificationToken.generate_token(user)
    
    # Get verification URL
    verification_url = token_obj.get_verification_url(request)
    
    # Prepare context
    context = {
        'user': user,
        'verification_url': verification_url,
        'expiry_hours': 24,  # Token expiry in hours
        'site_name': 'Restoran',
    }
    
    # Send email
    success = send_email_template(
        subject='Verify Your Email Address',
        template_name='email_verification',
        context=context,
        recipient_list=[user.email]
    )
    
    if success:
        # Log activity
        UserActivity.log_activity(
            user=user,
            activity_type='email_verification_sent',
            description='Email verification sent',
            request=request,
            metadata={'token_id': token_obj.id}
        )
    
    return success


def send_welcome_email(user):
    """
    Send a welcome email to a new user.
    
    Args:
        user: User object
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Prepare context
    context = {
        'user': user,
        'login_url': f"{settings.SITE_URL}{settings.LOGIN_URL}",
        'site_name': 'Restoran',
    }
    
    # Send email
    return send_email_template(
        subject='Welcome to Restoran!',
        template_name='welcome_email',
        context=context,
        recipient_list=[user.email]
    )


def process_referral(referrer_code, new_user):
    """
    Process a referral when a new user registers.
    
    Args:
        referrer_code: Referral code of the referring user
        new_user: Newly registered user
    
    Returns:
        ReferralBonus object if successful, None otherwise
    """
    # Find the referrer
    from django.contrib.auth.models import User
    try:
        referrer_profile = User.objects.get(profile__referral_code=referrer_code).profile
        referrer = referrer_profile.user
    except User.DoesNotExist:
        return None
    
    # Set the referred_by field on the new user's profile
    new_user.profile.referred_by = referrer
    new_user.profile.save(update_fields=['referred_by'])
    
    # Create a referral bonus
    expires_at = timezone.now() + datetime.timedelta(days=settings.REFERRAL_BONUS_EXPIRY_DAYS)
    bonus = ReferralBonus.objects.create(
        referrer=referrer,
        referred=new_user,
        bonus_type='points',
        bonus_value=settings.REFERRAL_POINTS_REWARD,
        status='pending',
        expires_at=expires_at,
        notes='Referral bonus for new user registration'
    )
    
    # Log activity for both users
    UserActivity.log_activity(
        user=referrer,
        activity_type='referral_created',
        description=f'Referred new user: {new_user.username}',
        metadata={'bonus_id': bonus.id}
    )
    
    UserActivity.log_activity(
        user=new_user,
        activity_type='referral_created',
        description=f'Registered using referral from: {referrer.username}',
        metadata={'bonus_id': bonus.id}
    )
    
    return bonus


def complete_referral(user):
    """
    Complete a referral after the referred user has verified their email.
    
    Args:
        user: User who was referred
    
    Returns:
        ReferralBonus object if successful, None otherwise
    """
    # Check if user was referred
    if not user.profile.referred_by:
        return None
    
    # Find pending referral bonus
    try:
        bonus = ReferralBonus.objects.get(
            referred=user,
            referrer=user.profile.referred_by,
            status='pending'
        )
    except ReferralBonus.DoesNotExist:
        return None
    
    # Redeem the bonus
    if bonus.redeem():
        # Log activity for both users
        UserActivity.log_activity(
            user=bonus.referrer,
            activity_type='referral_bonus_earned',
            description=f'Earned {int(bonus.bonus_value)} points for referring {user.username}',
            metadata={'bonus_id': bonus.id}
        )
        
        UserActivity.log_activity(
            user=user,
            activity_type='referral_completed',
            description=f'Completed referral from {bonus.referrer.username}',
            metadata={'bonus_id': bonus.id}
        )
        
        # Send email to referrer
        context = {
            'user': bonus.referrer,
            'referred_user': user,
            'bonus_points': int(bonus.bonus_value),
            'site_name': 'Restoran',
        }
        
        send_email_template(
            subject='You Earned Referral Points!',
            template_name='referral_bonus',
            context=context,
            recipient_list=[bonus.referrer.email]
        )
        
        return bonus
    
    return None
