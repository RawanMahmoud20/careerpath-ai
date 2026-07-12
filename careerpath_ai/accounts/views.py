from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .forms import NewRegisterForm, PasswordResetRequestForm, SetNewPasswordForm
from .models import EmailOTP


def send_otp_email(user):
    """Generate and send a fresh OTP to the user's email address."""
    otp_obj, _ = EmailOTP.objects.get_or_create(user=user)
    code = otp_obj.generate()

    subject = "Your CareerPath AI Verification Code"
    body = (
        f"Hi {user.full_name or user.username},\n\n"
        f"Your one-time verification code is:\n\n"
        f"  {code}\n\n"
        f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
        f"— The CareerPath AI Team"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = NewRegisterForm(request.POST)
        if form.is_valid():
            from .models import User
            # Clean up any stale pending account with the same username or email
            # (e.g. user registered but lost internet before verifying)
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            User.objects.filter(
                is_active=False, is_email_verified=False
            ).filter(
                Q(username=username) | Q(email=email)
            ).delete()

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.full_name = form.cleaned_data.get('full_name', '')
            user.is_active = False          # Inactive until email verified
            user.is_email_verified = False
            user.save()

            send_otp_email(user)

            request.session['pending_user_id'] = user.pk
            return redirect('verify_otp')
        else:
            pass   # form returned with .errors; template renders them inline per field
    else:
        form = NewRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_otp_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('signup')

    from .models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Resend OTP ──────────────────────────────────────────────
        if action == 'resend':
            send_otp_email(user)
            messages.info(request, "A new code has been sent to your email.")
            return redirect('verify_otp')

        # ── Verify OTP ──────────────────────────────────────────────
        entered_code = request.POST.get('otp', '').strip()
        otp_obj = getattr(user, 'email_otp', None)

        if otp_obj is None:
            messages.error(request, "No OTP found. Please request a new one.")
            return redirect('verify_otp')

        # Too many attempts?
        if otp_obj.attempts >= 5:
            messages.error(request, "Too many failed attempts. Please request a new code.")
            return redirect('verify_otp')

        if not otp_obj.is_valid():
            messages.error(request, "Your code has expired. Please request a new one.")
            return redirect('verify_otp')

        if entered_code != otp_obj.code:
            otp_obj.attempts += 1
            otp_obj.save()
            remaining = 5 - otp_obj.attempts
            messages.error(request, f"Incorrect code. {remaining} attempt(s) left.")
            return redirect('verify_otp')

        # ── Success ─────────────────────────────────────────────────
        user.is_active = True
        user.is_email_verified = True
        user.save()
        otp_obj.delete()
        del request.session['pending_user_id']

        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Email verified! Welcome to CareerPath AI ✨")
        return redirect('/dashboard/')

    return render(request, 'accounts/verify_otp.html', {'email': user.email})


def cancel_registration_view(request):
    """
    Called when user clicks 'Use a different email'.
    Deletes the pending (inactive, unverified) account so the
    email/username are freed, then redirects to the signup page.
    """
    from .models import User
    user_id = request.session.pop('pending_user_id', None)
    if user_id:
        try:
            user = User.objects.get(pk=user_id, is_active=False, is_email_verified=False)
            user.delete()
        except User.DoesNotExist:
            pass  # Already verified or doesn't exist — do nothing
    return redirect('signup')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # ── First: try normal authentication (for active users) ─────
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_email_verified:
                # Inactive or unverified, treat as verified? Wait.
                # The comment says: "Verified via admin / superuser — treat as verified"
                # Wait, if not user.is_email_verified:
                send_otp_email(user)
                request.session['pending_user_id'] = user.pk
                messages.info(request, "Please verify your email first. A new code has been sent.")
                return redirect('verify_otp')
            auth_login(request, user)
            return redirect('/dashboard/')

        # ── Second: check if the user exists but is pending verification ──
        # authenticate() returns None for inactive users, so we look up manually.
        # Try both username and email fields in case the user entered their email.
        from .models import User
        pending = User.objects.filter(
            is_active=False, is_email_verified=False
        ).filter(
            Q(username=username) | Q(email=username)
        ).first()

        if pending and pending.check_password(password):
            send_otp_email(pending)
            request.session['pending_user_id'] = pending.pk
            messages.info(request, "Your email isn't verified yet. We've sent a new code — please check your inbox.")
            return redirect('verify_otp')

        # ── Fallback: genuinely wrong credentials ────────────────────
        messages.error(request, "Invalid username or password.")
        form = AuthenticationForm()

    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('landing')


# ─────────────────────────────────────────────────────────────────────────────
# Password Reset – Step 1: Request a reset link
# ─────────────────────────────────────────────────────────────────────────────

def password_reset_request_view(request):
    """User enters their email; we send a secure one-time reset link."""
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            from .models import User
            user = User.objects.filter(email__iexact=email, is_active=True).first()

            if user:
                uid   = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    f'/accounts/reset-password/{uid}/{token}/'
                )

                subject = "Reset your CareerPath AI password"
                body = (
                    f"Hi {user.full_name or user.username},\n\n"
                    f"We received a request to reset the password for your account.\n\n"
                    f"Click the link below to set a new password (expires in 1 hour):\n\n"
                    f"  {reset_url}\n\n"
                    f"If you didn't request this, you can safely ignore this email.\n\n"
                    f"— The CareerPath AI Team"
                )
                send_mail(
                    subject, body, settings.DEFAULT_FROM_EMAIL,
                    [user.email], fail_silently=False,
                )

            # Always show the same message to avoid email enumeration
            messages.success(
                request,
                "If that email address is registered, you'll receive a reset link shortly."
            )
            return redirect('password_reset_request')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


# ─────────────────────────────────────────────────────────────────────────────
# Password Reset – Step 2: Consume the link & set new password
# ─────────────────────────────────────────────────────────────────────────────

def password_reset_confirm_view(request, uidb64, token):
    """Validate the reset token and let the user choose a new password."""
    from .models import User

    # Decode the user pk
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Validate the token
    token_valid = user is not None and default_token_generator.check_token(user, token)

    if not token_valid:
        messages.error(
            request,
            "This password reset link is invalid or has expired. Please request a new one."
        )
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            # Make sure the account is fully active (edge case: reset before verification)
            user.is_active = True
            user.is_email_verified = True
            user.save()
            messages.success(
                request,
                "Your password has been updated. You can now log in with your new password."
            )
            return redirect('login')
        # form errors will be shown in template
    else:
        form = SetNewPasswordForm()

    return render(request, 'accounts/password_reset_confirm.html', {
        'form': form,
        'uidb64': uidb64,
        'token': token,
    })