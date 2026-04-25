from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # Removed is_staff as it's not required for this setup
    pass
