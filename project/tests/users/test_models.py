import pytest
from django.core.exceptions import FieldDoesNotExist

from config.users.models import CustomUser


@pytest.mark.django_db
class TestCustomUserManager:
    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="Email field must be set"):
            CustomUser.objects.create_user(email=None, password="pass123")

    def test_create_user_normalizes_email(self):
        user = CustomUser.objects.create_user(
            email="Test@EXAMPLE.COM",
            password="pass123",
        )
        assert user.email == "Test@example.com"

    def test_create_user_sets_hashed_password(self):
        user = CustomUser.objects.create_user(
            email="user@example.com",
            password="pass123",
        )
        assert user.password != "pass123"
        assert user.check_password("pass123") is True

    def test_create_superuser_sets_flags(self):
        user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="pass123",
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_create_superuser_rejects_is_staff_false(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            CustomUser.objects.create_superuser(
                email="admin2@example.com",
                password="pass123",
                is_staff=False,
            )

    def test_create_superuser_rejects_is_superuser_false(self):
        with pytest.raises(ValueError, match="is_superuser=True"):
            CustomUser.objects.create_superuser(
                email="admin3@example.com",
                password="pass123",
                is_superuser=False,
            )


@pytest.mark.django_db
class TestCustomUserModel:
    def test_username_field_removed(self):
        with pytest.raises(FieldDoesNotExist):
            CustomUser._meta.get_field("username")

    def test_username_field_is_email(self):
        assert CustomUser.USERNAME_FIELD == "email"

    def test_str_returns_email(self):
        user = CustomUser.objects.create_user(
            email="user2@example.com",
            password="pass123",
        )
        assert str(user) == "user2@example.com"
