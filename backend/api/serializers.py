from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import ConsultationReport
# Make sure to import CustomUser if it's in the same app's models.py
# from .models import CustomUser

User = get_user_model() # Dynamically get the active user model (CustomUser in this case)

# User Serializer for read-only user data
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role", "hospital"]

# Register Serializer for creating new user accounts
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Fields required for registration, now explicitly including first_name and last_name
        fields = ["first_name", "last_name", "email", "password", "role", "hospital"]
        # Extra kwargs for password security and making hospital optional
        extra_kwargs = {
            "password": {"write_only": True}, # Password should not be returned in responses
            "hospital": {"required": False, "allow_blank": True, "allow_null": True}, # Hospital is optional
            "first_name": {"required": True}, # Ensuring first_name is explicitly required
            "last_name": {"required": True},  # Ensuring last_name is explicitly required
        }

    def create(self, validated_data):
        # Extract first_name, last_name, role, and hospital
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        role = validated_data.pop('role', 'patient')
        hospital = validated_data.pop('hospital', None)

        # Use create_user to ensure the password is hashed correctly
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            role=role,
            hospital=hospital,
        )
        return user

# Login Serializer to authenticate users and generate JWT tokens
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # Authenticate user using email and password
        user = authenticate(username=email, password=password) # username here refers to USERNAME_FIELD

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # You might want to generate tokens here or in a view,
        # but for now, just returning the user is sufficient for validation.
        return {"user": user}

# ConsultationReport Serializer for handling consultation report data
class ConsultationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationReport
        fields = ['id', 'user', 'responses', 'ml_result', 'created_at']
        # These fields are set by the server, not directly by the client in a POST/PUT
        read_only_fields = ['user', 'created_at']

