from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from accounts.models import EmailOTP

User = get_user_model()

class AuthenticationTestCase(TestCase):
    def test_registration_and_otp_verification(self):
        # 1. Register a new user
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'Password123_456',
            'password2': 'Password123_456',
        })
        # Should redirect to verify_otp
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('verify_otp'))

        # Check user is created but inactive
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)

        # Check OTP was generated and email sent
        otp_obj = EmailOTP.objects.get(user=user)
        self.assertIsNotNone(otp_obj.code)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp_obj.code, mail.outbox[0].body)

        # 2. Verify with incorrect OTP
        session = self.client.session
        session['pending_user_id'] = user.pk
        session.save()

        response = self.client.post(reverse('verify_otp'), {
            'action': 'verify',
            'otp': '000000',
        })
        self.assertEqual(response.status_code, 302) # redirects to verify_otp
        otp_obj.refresh_from_db()
        self.assertEqual(otp_obj.attempts, 1)

        # 3. Verify with correct OTP
        response = self.client.post(reverse('verify_otp'), {
            'action': 'verify',
            'otp': otp_obj.code,
        })
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_password_reset(self):
        # Create an active user first
        user = User.objects.create_user(
            username='activeuser',
            email='active@example.com',
            password='OldPassword123_456',
            is_active=True,
            is_email_verified=True
        )

        # Send password reset request
        response = self.client.post(reverse('password_reset_request'), {
            'email': 'active@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        # Retrieve the URL from the email body
        email_body = mail.outbox[0].body
        # Extract reset link token/uid
        # Link pattern: /accounts/reset-password/<uidb64>/<token>/
        import re
        match = re.search(r'/accounts/reset-password/([^/]+)/([^/]+)/', email_body)
        self.assertIsNotNone(match)
        uidb64 = match.group(1)
        token = match.group(2)

        # Confirm setting new password
        response = self.client.post(reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token}), {
            'password': 'NewPassword123_456',
            'password2': 'NewPassword123_456',
        })
        self.assertEqual(response.status_code, 302)

        # Try logging in with the new password
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword123_456'))
