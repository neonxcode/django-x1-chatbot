from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class UserAuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_user_username = 'testuser'
        self.test_user_password = 'testpassword123'
        self.test_user_email = 'testuser@example.com'

        # Create a dummy image file for signup
        self.dummy_image = SimpleUploadedFile(
            name='test_image.png',
            content=b'GIF89a\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/png'
        )
        
        # It's good practice to ensure no users from previous tests exist if tests are not isolated
        # However, Django's TestCase runs each test in its own transaction, so this is usually not needed.
        # User.objects.all().delete()


    def test_user_signup(self):
        """Test user registration."""
        signup_url = reverse('signup')
        user_count_before = User.objects.count()

        form_data = {
            'username': self.test_user_username,
            'first_name': 'Test',
            'last_name': 'User',
            'email': self.test_user_email,
            'password1': self.test_user_password,
            'password2': self.test_user_password,
            'image': self.dummy_image,
        }
        
        response = self.client.post(signup_url, data=form_data)

        self.assertEqual(User.objects.count(), user_count_before + 1, "User should be created")
        new_user = User.objects.get(username=self.test_user_username)
        self.assertIsNotNone(new_user, "New user object should exist")
        self.assertEqual(new_user.email, self.test_user_email) # Check email was saved

        # Signup view logs the user in and redirects to 'index'.
        # 'index' then redirects to 'chat:emptyChat'.
        # 1. Check the first redirect (from signup to 'index')
        self.assertEqual(response.status_code, 302, "Signup POST should return 302")
        self.assertEqual(response.url, reverse('index'), "Signup POST should redirect to 'index'")

        # 2. Manually follow the redirect from 'index'
        index_response = self.client.get(reverse('index'))
        # 'index' for an authenticated user should redirect to 'chat:emptyChat'
        self.assertEqual(index_response.status_code, 302, "'index' view should redirect for authenticated user")
        self.assertEqual(index_response.url, reverse('chat:emptyChat'), "'index' view should redirect to 'chat:emptyChat'")

        # 3. Check the final page status
        final_response = self.client.get(reverse('chat:emptyChat'))
        self.assertEqual(final_response.status_code, 200, "'chat:emptyChat' page should return 200")
        
        # Check if user is logged in after signup
        self.assertTrue('_auth_user_id' in self.client.session, "User should be logged in after signup")


    def test_user_login(self):
        """Test user login."""
        # Create a user to log in with
        User.objects.create_user(
            username=self.test_user_username,
            password=self.test_user_password,
            email=self.test_user_email
        )
        login_url = reverse('login')

        # Attempt login with correct credentials
        response = self.client.post(login_url, {
            'username': self.test_user_username,
            'password': self.test_user_password,
        })
        # 1. Check the first redirect (from login to 'index')
        self.assertEqual(response.status_code, 302, "Login POST should return 302")
        self.assertEqual(response.url, reverse('index'), "Login POST should redirect to 'index'")

        # 2. Manually follow the redirect from 'index'
        index_response = self.client.get(reverse('index'))
        # 'index' for an authenticated user should redirect to 'chat:emptyChat'
        self.assertEqual(index_response.status_code, 302, "'index' view should redirect for authenticated user")
        self.assertEqual(index_response.url, reverse('chat:emptyChat'), "'index' view should redirect to 'chat:emptyChat'")
        
        # 3. Check the final page status
        final_response = self.client.get(reverse('chat:emptyChat'))
        self.assertEqual(final_response.status_code, 200, "'chat:emptyChat' page should return 200")

        self.assertTrue('_auth_user_id' in self.client.session, "User should be in session after correct login")

        # Attempt login with incorrect password
        self.client.logout() # Ensure previous session is cleared
        response_fail = self.client.post(login_url, {
            'username': self.test_user_username,
            'password': 'wrongpassword',
        })
        self.assertEqual(response_fail.status_code, 200, "Failed login should re-render login page")
        self.assertFalse('_auth_user_id' in self.client.session, "User should not be in session after incorrect login")
        self.assertContains(response_fail, "Incorrect Login Details.", msg_prefix="Error message should be displayed on failed login")

        # Attempt login with non-existent user
        self.client.logout()
        response_nonexistent = self.client.post(login_url, {
            'username': 'nouser',
            'password': 'anypassword',
        })
        self.assertEqual(response_nonexistent.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertContains(response_nonexistent, "Incorrect Login Details.")


    def test_user_logout(self):
        """Test user logout."""
        # Create a user and log them in
        User.objects.create_user(username=self.test_user_username, password=self.test_user_password)
        self.client.login(username=self.test_user_username, password=self.test_user_password)
        self.assertTrue('_auth_user_id' in self.client.session, "User should be logged in before logout test")

        logout_url = reverse('logout')
        response = self.client.get(logout_url)
        
        # Logout view redirects to 'login'
        self.assertRedirects(response, reverse('login'), msg_prefix="Logout should redirect to login page")
        self.assertFalse('_auth_user_id' in self.client.session, "User should not be in session after logout")

    def tearDown(self):
        # Clean up created media files if any (though SimpleUploadedFile is in memory)
        # Example: if actual files were created in media directory during tests
        pass
