from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Custom User Manager to handle user creation with email as the unique identifier
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'doctor') # Superusers can be doctors by default or another admin role

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


# CustomUser model extending AbstractUser to add roles and hospital info
class CustomUser(AbstractUser):
    # Explicitly remove the default username field from AbstractUser
    # We will use email as the primary identification field.
    username = None

    # Define choices for user roles
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    # Role field with choices, defaults to 'patient'
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    # Hospital field, optional for doctors
    hospital = models.CharField(max_length=255, blank=True, null=True)
    # Email field, ensuring uniqueness and used for authentication
    email = models.EmailField(unique=True)

    # Set email as the field used for unique identification (username for AbstractUser logic)
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    # Define required fields when creating a user (e.g., via createsuperuser command)
    # Since 'username' is now None, we remove it from REQUIRED_FIELDS.
    # AbstractUser still has 'first_name' and 'last_name', so we'll keep them as required for superuser.
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Assign the custom manager to the objects attribute
    objects = CustomUserManager()

    def __str__(self):
        # Human-readable representation of the user
        return f"{self.email} - {self.role}"

# ConsultationReport model to store detailed consultation data
class ConsultationReport(models.Model):
    # Foreign Key to CustomUser, linking a report to a specific user
    # Allows for null and blank to handle cases where a user might be deleted
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    # JSONField to store flexible, semi-structured responses (e.g., patient's answers)
    responses = models.JSONField()
    # TextField for storing machine learning analysis results, with a default value
    ml_result = models.TextField(default="Not Available")
    # Automatically records the creation timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Human-readable representation of the consultation report
        user_email = self.user.email if self.user else "N/A"
        return f"Consultation Report {self.id} - User {user_email}"
