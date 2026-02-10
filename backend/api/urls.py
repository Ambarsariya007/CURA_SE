from django.urls import path
from .views import get_user_data,RegisterView, LoginView, UserDetailView, csrf_token_view, logout_view, save_consultation, generate_pdf, predict_disease_api, serve_medical_book # Import all views used

urlpatterns = [
    # User authentication and management
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('user/', UserDetailView.as_view(), name='api-user'), # Assuming UserDetailView exists for current user info
    path("get_user/", get_user_data, name="get_user_data"), # Assuming get_user_data function exists
    path("logout/", logout_view, name="logout"),
    path("csrf/", csrf_token_view, name="csrf_token"),

    # Consultation and AI related APIs
    path('api/save-consultation/', save_consultation, name='save-consultation'), # Assuming save_consultation function exists
    path("api/generate-report/<int:report_id>/", generate_pdf, name="generate-pdf"), # Assuming generate_pdf function exists
    path('api/predict-diseases/', predict_disease_api, name='predict_disease_api'), # Assuming predict_disease_api function exists
    path('api/medical-books/<str:book_name>/', serve_medical_book, name='serve-medical-book'),
]
