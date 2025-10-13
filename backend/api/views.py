from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.contrib.auth import logout
from rest_framework.authtoken.models import Token # Used for Token authentication
from django.views.decorators.csrf import csrf_exempt # Use with caution, mostly for debugging or specific endpoints

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer # Import the serializers
from .models import CustomUser, ConsultationReport # Import your models
# from .utils import save_consultation, generate_pdf, predict_disease_api # Assuming these are defined elsewhere or will be defined.

# Get the custom user model
User = get_user_model()

# --- Authentication Views ---

class RegisterView(APIView):
    permission_classes = [AllowAny] # Allow anyone to register

    def post(self, request):
        print("Incoming Registration Data:", request.data) # Log incoming data for debugging

        # Use the RegisterSerializer to validate and create the user
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True): # Raise exception automatically returns 400 with errors
            user = serializer.save() # The serializer's create method handles password hashing and custom fields
            # You might want to return a token or specific user data here as well
            return Response({"message": "Registration successful", "email": user.email}, status=status.HTTP_201_CREATED)
        # This part is technically unreachable if raise_exception=True is used, but good for explicit return
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny] # Allow anyone to attempt login

    def post(self, request):
        print("Incoming Login Data:", request.data) # Log incoming data

        # Use the LoginSerializer for validation and authentication
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user'] # Get the authenticated user from the serializer

            # Generate or retrieve the token for the authenticated user
            token, created = Token.objects.get_or_create(user=user)

            # Return token and user details
            return Response({
                "token": token.key,
                "user": {
                    "id": user.id,
                    "first_name": user.first_name, # Return first name
                    "last_name": user.last_name,   # Return last name
                    "email": user.email,
                    "role": user.role,
                    "hospital": user.hospital,
                }
            }, status=status.HTTP_200_OK)
        # Unreachable if raise_exception=True
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can access their own details

    def get(self, request):
        # The authenticated user is available via request.user
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# --- Utility Views ---

def csrf_token_view(request):
    """Returns the CSRF token."""
    token = get_token(request)
    return JsonResponse({"csrfToken": token})

@csrf_exempt # Consider removing this in production and properly handling CSRF tokens on frontend
def logout_view(request):
    """Logs out the user and deletes their session."""
    if request.method == "POST":
        if request.user.is_authenticated:
            # Delete the authentication token if using Token authentication
            Token.objects.filter(user=request.user).delete()
            logout(request) # Log out the user from the Django session
            response = JsonResponse({"message": "Logged out successfully"})
            response.delete_cookie("sessionid") # Ensure session cookie is cleared
            return response
        return JsonResponse({"error": "No user logged in."}, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({"error": "Invalid request method. Use POST."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# --- Placeholder for AI/Consultation related functions ---
# You'll need to define these functions or classes in your views.py
# or import them from another file if they are complex.

# Example placeholder for get_user_data (if it's not handled by UserDetailView)
from rest_framework.decorators import api_view, permission_classes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# Example placeholder for save_consultation
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_consultation(request):
    # This would likely use ConsultationReportSerializer
    report_data = request.data
    report_data['user'] = request.user.id # Assign the current user
    serializer = ConsultationReportSerializer(data=report_data)
    if serializer.is_valid(raise_exception=True):
        serializer.save(user=request.user) # Ensure user is saved to the report
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Example placeholder for generate_pdf
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_pdf(request, report_id):
    # Logic to fetch ConsultationReport by report_id and generate PDF
    try:
        report = ConsultationReport.objects.get(id=report_id, user=request.user)
        # Placeholder for actual PDF generation logic
        # For now, just a success message
        return Response({"message": f"PDF generated for report {report_id}."}, status=status.HTTP_200_OK)
    except ConsultationReport.DoesNotExist:
        return Response({"error": "Report not found or not owned by user."}, status=status.HTTP_404_NOT_FOUND)

# Example placeholder for predict_disease_api
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_disease_api(request):
    # Logic to get symptoms from request.data and call ML model
    symptoms = request.data.get('symptoms')
    if not symptoms:
        return Response({"error": "Symptoms data is required."}, status=status.HTTP_400_BAD_REQUEST)
    # Placeholder for ML prediction
    ml_prediction = f"Predicted disease based on symptoms: {symptoms} (This is a dummy prediction)."
    return Response({"prediction": ml_prediction}, status=status.HTTP_200_OK)




    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        response["Access-Control-Allow-Credentials"] = "true"
        return response
class CheckAuthView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                "authenticated": True,
                "user": {
                    "id": request.user.id,
                    "email": request.user.email
                }
            }, status=status.HTTP_200_OK)
        return Response({"authenticated": False}, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout

class LogoutView(APIView):
    def post(self, request):
        # Perform logout
        logout(request)
        
        # Clear session data
        request.session.flush()
        
        return Response({"success": True, "message": "Logout successful"}, status=status.HTTP_200_OK)

    

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.contrib.auth.decorators import login_required

@login_required
def get_user(request):
    if request.user.is_authenticated:
        return JsonResponse({"username": request.user.username})
    return JsonResponse({"error": "User not authenticated"}, status=401)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse

def get_user_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    
    user = request.user
    return JsonResponse({
        "username": user.username,
        "email": user.email
    })

from django.contrib.auth import logout
from django.http import JsonResponse

def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logged out successfully"}, status=200)

from .models import ConsultationReport

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ConsultationReport

import logging

import json
import logging
from django.http import JsonResponse
from .models import ConsultationReport
from django.views.decorators.csrf import csrf_exempt

def save_consultation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logging.info(f"Received data: {data}")  # Log received data for debugging

            user_id = data.get("user_id", None)
            responses = data.get("responses", {})
            ml_result = data.get("mlResult", "Not Available")

            # Additional validation logs
            logging.info(f"User ID: {user_id}")
            logging.info(f"Responses: {responses}")
            logging.info(f"ML Result: {ml_result}")

            # Save data in the database
            report = ConsultationReport.objects.create(
                user_id=user_id,
                responses=responses,
                ml_result=ml_result
            )

            return JsonResponse({"message": "Consultation saved successfully!", "report_id": report.id}, status=201)

        except Exception as e:
            logging.error(f"Error saving consultation: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)



from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json
from .models import ConsultationReport

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import ConsultationReport

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from django.http import HttpResponse
from .models import ConsultationReport

def generate_pdf(request, report_id):
    try:
        # Fetch the report data from the database
        report = ConsultationReport.objects.get(id=report_id)
        print(f"🔍 ML Result raw data: {report.ml_result}")
        print(f"🔍 ML Result type: {type(report.ml_result)}")

        # Create an HTTP response with a PDF file
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="consultation_report_{report_id}.pdf"'

        # Define modern color scheme
        primary_color = colors.HexColor('#1E88E5')  # Modern blue
        secondary_color = colors.HexColor('#43A047')  # Modern green
        text_color = colors.HexColor('#212121')  # Near black
        light_bg = colors.HexColor('#F5F5F5')  # Very light gray

        # Create PDF document with margins
        doc = SimpleDocTemplate(
            response, 
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()

        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=primary_color,
            spaceAfter=16,
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=secondary_color,
            spaceAfter=12
        )
        
        # Modified section_title style to ensure it's not italicized
        section_title = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=text_color,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',  # Using regular bold font instead of potentially italic
            italic=0  # Explicitly setting italic to 0 (off)
        )
        
        body_text = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=text_color,
            leading=14
        )

        # Header with modern styling
        cura_header = Paragraph(
            "<font color='#1E88E5'><b>CURA</b></font> <font color='#43A047'>Health Consultation</font>",
            title_style
        )
        elements.append(cura_header)
        
        # Report subtitle
        report_title = Paragraph(
            f"Consultation Report #{report.id}",
            subtitle_style
        )
        elements.append(report_title)
        
        # Date & time info
        if hasattr(report, 'created_at'):
            date_info = Paragraph(
                f"Generated on: {report.created_at.strftime('%B %d, %Y at %H:%M')}",
                body_text
            )
            elements.append(date_info)
        
        elements.append(Spacer(1, 20))
        
        # Horizontal separator
        separator_style = TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 1, primary_color),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ])
        separator = Table([['']],  colWidths=[7*inch])
        separator.setStyle(separator_style)
        elements.append(separator)
        elements.append(Spacer(1, 20))

        # Basic Information Section with modern table - non-italicized section title
        elements.append(Paragraph("Report Summary", section_title))
        elements.append(Spacer(1, 6))
        try:
            ml_data = json.loads(report.ml_result)
            predicted_diseases = ml_data.get("predicted_diseases", []) # Top 3
            top_disease_names = ", ".join(predicted_diseases)
        except Exception:
            top_disease_names = "N/A"

        user_info = [
            [Paragraph("<b>Report ID:</b>", body_text), Paragraph(str(report.id), body_text)],
            [Paragraph("<b>ML Diagnosis:</b>", body_text), Paragraph(top_disease_names, body_text)],
        ]


        # Modern table with clean styling
        table = Table(user_info, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([ 
            # Headers
            ('BACKGROUND', (0, 0), (0, -1), light_bg),
            ('TEXTCOLOR', (0, 0), (0, -1), text_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Content
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            # Border styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30))

        # User Responses Section with modern styling - non-italicized section title
        if report.responses:
            elements.append(Paragraph("Consultation Responses", section_title))
            elements.append(Spacer(1, 6))
            
            # Create enhanced header row
            response_data = [
                [Paragraph("<b>Question</b>", body_text), 
                 Paragraph("<b>Response</b>", body_text)]
            ]
            
            # Add each Q&A row with enhanced styling
            for q, a in report.responses.items():
                question_text = Paragraph(q, body_text)
                answer_text = Paragraph(a, body_text)
                response_data.append([question_text, answer_text])

            response_table = Table(response_data, colWidths=[3.25*inch, 3.25*inch])
            
            # Create dynamic alternating row styles
            table_style = [
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Grid styling
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]
            
            # Add alternating row colors dynamically based on available rows
            for i in range(1, len(response_data)):
                if i % 2 == 0:  # Even rows (starting from 1-based index)
                    table_style.append(('BACKGROUND', (0, i), (-1, i), light_bg))
                else:  # Odd rows
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            
            response_table.setStyle(TableStyle(table_style))
            elements.append(response_table)
            elements.append(Spacer(1, 30))

        # Add disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Italic'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        disclaimer = Paragraph(
            "This report is computer-generated and may require review by a healthcare professional. "
            "CURA's ML diagnosis is not a substitute for professional medical advice.",
            disclaimer_style
        )
        elements.append(disclaimer)
        elements.append(Spacer(1, 12))
        
        # Modern footer with separator
        footer_separator = Table([['']],  colWidths=[7*inch])
        footer_separator.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
        ]))
        elements.append(footer_separator)
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=secondary_color,
            alignment=1  # Center alignment
        )
        footer = Paragraph(
            "Thank you for using <b>CURA</b> Health Consultation Platform | Stay Healthy",
            footer_style
        )
        elements.append(Spacer(1, 8))
        elements.append(footer)

        # Build the PDF
        doc.build(elements)
        return response

    except ConsultationReport.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


import torch
import numpy as np
import pandas as pd
from torch import nn
# Load indexes (Manually copy the dictionary from your dataset)
disease_indexes = {'Fungal infection': 0, 'Allergy': 1, 'GERD': 2, 'Chronic cholestasis': 3, 'Drug Reaction': 4,
                   'Peptic ulcer diseae': 5, 'AIDS': 6, 'Diabetes ': 7, 'Gastroenteritis': 8, 'Bronchial Asthma': 9,
                   'Hypertension ': 10, 'Migraine': 11, 'Cervical spondylosis': 12, 'Paralysis (brain hemorrhage)': 13,
                   'Jaundice': 14, 'Malaria': 15, 'Chicken pox': 16, 'Dengue': 17, 'Typhoid': 18, 'hepatitis A': 19,
                   'Hepatitis B': 20, 'Hepatitis C': 21, 'Hepatitis D': 22, 'Hepatitis E': 23, 'Alcoholic hepatitis': 24,
                   'Tuberculosis': 25, 'Common Cold': 26, 'Pneumonia': 27, 'Dimorphic hemmorhoids(piles)': 28, 'Heart attack': 29,
                   'Varicose veins': 30, 'Hypothyroidism': 31, 'Hyperthyroidism': 32, 'Hypoglycemia': 33, 'Osteoarthristis': 34,
                   'Arthritis': 35, '(vertigo) Paroymsal  Positional Vertigo': 36, 'Acne': 37, 'Urinary tract infection': 38,
                   'Psoriasis': 39, 'Impetigo': 40}

symptom_indexes = {' abdominal_pain': 0, ' abnormal_menstruation': 1, ' acidity': 2, ' acute_liver_failure': 3, ' altered_sensorium': 4, ' anxiety': 5, ' back_pain': 6, ' belly_pain': 7, ' blackheads': 8, ' bladder_discomfort': 9, ' blister': 10, ' blood_in_sputum': 11, ' bloody_stool': 12, ' blurred_and_distorted_vision': 13, ' breathlessness': 14, ' brittle_nails': 15, ' bruising': 16, ' burning_micturition': 17, ' chest_pain': 18, ' chills': 19, ' cold_hands_and_feets': 20, ' coma': 21, ' congestion': 22, ' constipation': 23, ' continuous_feel_of_urine': 24, ' continuous_sneezing': 25, ' cough': 26, ' cramps': 27, ' dark_urine': 28, ' dehydration': 29, ' depression': 30, ' diarrhoea': 31, ' dischromic _patches': 32, ' distention_of_abdomen': 33, ' dizziness': 34, ' drying_and_tingling_lips': 35, ' enlarged_thyroid': 36, ' excessive_hunger': 37, ' extra_marital_contacts': 38, ' family_history': 39, ' fast_heart_rate': 40, ' fatigue': 41, ' fluid_overload': 42, ' foul_smell_of urine': 43, ' headache': 44, ' high_fever': 45, ' hip_joint_pain': 46, ' history_of_alcohol_consumption': 47, ' increased_appetite': 48, ' indigestion': 49, ' inflammatory_nails': 50, ' internal_itching': 51, ' irregular_sugar_level': 52, ' irritability': 53, ' irritation_in_anus': 54, ' joint_pain': 55, ' knee_pain': 56, ' lack_of_concentration': 57, ' lethargy': 58, ' loss_of_appetite': 59, ' loss_of_balance': 60, ' loss_of_smell': 61, ' malaise': 62, ' mild_fever': 63, ' mood_swings': 64, ' movement_stiffness': 65, ' mucoid_sputum': 66, ' muscle_pain': 67, ' muscle_wasting': 68, ' muscle_weakness': 69, ' nausea': 70, ' neck_pain': 71, ' nodal_skin_eruptions': 72, ' obesity': 73, ' pain_behind_the_eyes': 74, ' pain_during_bowel_movements': 75, ' pain_in_anal_region': 76, ' painful_walking': 77, ' palpitations': 78, ' passage_of_gases': 79, ' patches_in_throat': 80, ' phlegm': 81, ' polyuria': 82, ' prominent_veins_on_calf': 83, ' puffy_face_and_eyes': 84, ' pus_filled_pimples': 85, ' receiving_blood_transfusion': 86, ' receiving_unsterile_injections': 87, ' red_sore_around_nose': 88, ' red_spots_over_body': 89, ' redness_of_eyes': 90, ' restlessness': 91, ' runny_nose': 92, ' rusty_sputum': 93, ' scurring': 94, ' shivering': 95, ' silver_like_dusting': 96, ' sinus_pressure': 97, ' skin_peeling': 98, ' skin_rash': 99, ' slurred_speech': 100, ' small_dents_in_nails': 101, ' spinning_movements': 102, ' spotting_ urination': 103, ' stiff_neck': 104, ' stomach_bleeding': 105, ' stomach_pain': 106, ' sunken_eyes': 107, ' sweating': 108, ' swelled_lymph_nodes': 109, ' swelling_joints': 110, ' swelling_of_stomach': 111, ' swollen_blood_vessels': 112, ' swollen_extremeties': 113, ' swollen_legs': 114, ' throat_irritation': 115, ' toxic_look_(typhos)': 116, ' ulcers_on_tongue': 117, ' unsteadiness': 118, ' visual_disturbances': 119, ' vomiting': 120, ' watering_from_eyes': 121, ' weakness_in_limbs': 122, ' weakness_of_one_body_side': 123, ' weight_gain': 124, ' weight_loss': 125, ' yellow_crust_ooze': 126, ' yellow_urine': 127, ' yellowing_of_eyes': 128, ' yellowish_skin': 129, '(vertigo) Paroymsal  Positional Vertigo': 130, 'AIDS': 131, 'Acne': 132, 'Alcoholic hepatitis': 133, 'Allergy': 134, 'Arthritis': 135, 'Bronchial Asthma': 136, 'Cervical spondylosis': 137, 'Chicken pox': 138, 'Chronic cholestasis': 139, 'Common Cold': 140, 'Dengue': 141, 'Diabetes ': 142, 'Dimorphic hemmorhoids(piles)': 143, 'Drug Reaction': 144, 'Fungal infection': 145, 'GERD': 146, 'Gastroenteritis': 147, 'Heart attack': 148, 'Hepatitis B': 149, 'Hepatitis C': 150, 'Hepatitis D': 151, 'Hepatitis E': 152, 'Hypertension ': 153, 'Hyperthyroidism': 154, 'Hypoglycemia': 155, 'Hypothyroidism': 156, 'Impetigo': 157, 'Jaundice': 158, 'Malaria': 159, 'Migraine': 160, 'Osteoarthristis': 161, 'Paralysis (brain hemorrhage)': 162, 'Peptic ulcer diseae': 163, 'Pneumonia': 164, 'Psoriasis': 165, 'Tuberculosis': 166, 'Typhoid': 167, 'Urinary tract infection': 168, 'Varicose veins': 169, 'hepatitis A': 170, 'itching': 171}

# Load trained model
class SymptomClassifier(nn.Module):
    def __init__(self, input_size: int, num_classes: int):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(in_features=input_size, out_features=128),
            nn.ReLU(),
            nn.Linear(in_features=128, out_features=64),
            nn.Tanh(),
            nn.Linear(in_features=64, out_features=num_classes)
        )
        
    def forward(self, input):
        return self.model(input)

# Initialize Model
input_size = len(symptom_indexes)
num_classes = len(disease_indexes)
classifier = SymptomClassifier(input_size, num_classes)

# Load model weights
classifier.load_state_dict(torch.load("bhsoda.pth"))
classifier.eval()

# Function to predict disease from symptoms
def predict_disease(symptom_indexes_list, top_k=3):
    # Create symptom vector
    input_vector = np.zeros(len(symptom_indexes))  # Initialize all symptoms as 0
    associated_symptoms = []  # Store actual symptom names

    for idx in symptom_indexes_list:
        if 0 <= idx < len(symptom_indexes):  # Ensure the index is valid
            input_vector[idx] = 1
            symptom_name = list(symptom_indexes.keys())[list(symptom_indexes.values()).index(idx)]
            associated_symptoms.append(symptom_name)
        else:
            print(f"Warning: Symptom index '{idx}' is out of range.")

    # Convert to tensor
    input_tensor = torch.Tensor(input_vector).unsqueeze(0)  # Add batch dimension
    
    # Make prediction
    with torch.no_grad():
        output = classifier(input_tensor)  # Get raw logits
        probabilities = torch.softmax(output, dim=-1)  # Convert logits to probabilities
        top_probs, top_indices = torch.topk(probabilities, top_k, dim=-1)  # Get top-k predictions
    
    # Extract top-k predictions
    top_probs = top_probs.squeeze().tolist()  # Convert tensor to list
    top_indices = top_indices.squeeze().tolist()  # Convert tensor to list

    # Map indices to disease names
    top_diseases = [(list(disease_indexes.keys())[list(disease_indexes.values()).index(idx)], prob * 100) 
                    for idx, prob in zip(top_indices, top_probs)]

    # Print the associated symptoms
    '''
    print("Symptoms Associated with Input:")
    for symptom in associated_symptoms:
        print(f"- {symptom}")

    print("\nTop Predicted Diseases:")
    for disease, prob in top_diseases:
        print(f"{disease}")
    '''
    
    finalstring = str(associated_symptoms) + "\n" + str(top_diseases)
    reccomendation = reccomender.generate_reccomendation(finalstring)
    return reccomendation
    





import google.generativeai as genai
import re
import json

# Secure API Key (Store in Environment Variables Instead)
genai.configure(api_key="AIzaSyASjCwVvZUCK6WdC03nQm-1pM8aSAy5WCo")

import google.generativeai as genai

# Configure Gemini with a working model
genai.configure(api_key="AIzaSyASjCwVvZUCK6WdC03nQm-1pM8aSAy5WCo")
model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

print("✅ Gemini model configured: gemini-2.0-flash-exp")

context = {' abdominal_pain': 0, ' abnormal_menstruation': 1, ' acidity': 2, ' acute_liver_failure': 3, ' altered_sensorium': 4, ' anxiety': 5, ' back_pain': 6, ' belly_pain': 7, ' blackheads': 8, ' bladder_discomfort': 9, ' blister': 10, ' blood_in_sputum': 11, ' bloody_stool': 12, ' blurred_and_distorted_vision': 13, ' breathlessness': 14, ' brittle_nails': 15, ' bruising': 16, ' burning_micturition': 17, ' chest_pain': 18, ' chills': 19, ' cold_hands_and_feets': 20, ' coma': 21, ' congestion': 22, ' constipation': 23, ' continuous_feel_of_urine': 24, ' continuous_sneezing': 25, ' cough': 26, ' cramps': 27, ' dark_urine': 28, ' dehydration': 29, ' depression': 30, ' diarrhoea': 31, ' dischromic patches': 32, ' distention_of_abdomen': 33, ' dizziness': 34, ' drying_and_tingling_lips': 35, ' enlarged_thyroid': 36, ' excessive_hunger': 37, ' extra_marital_contacts': 38, ' family_history': 39, ' fast_heart_rate': 40, ' fatigue': 41, ' fluid_overload': 42, ' foul_smell_of urine': 43, ' headache': 44, ' high_fever': 45, ' hip_joint_pain': 46, ' history_of_alcohol_consumption': 47, ' increased_appetite': 48, ' indigestion': 49, ' inflammatory_nails': 50, ' internal_itching': 51, ' irregular_sugar_level': 52, ' irritability': 53, ' irritation_in_anus': 54, ' joint_pain': 55, ' knee_pain': 56, ' lack_of_concentration': 57, ' lethargy': 58, ' loss_of_appetite': 59, ' loss_of_balance': 60, ' loss_of_smell': 61, ' malaise': 62, ' mild_fever': 63, ' mood_swings': 64, ' movement_stiffness': 65, ' mucoid_sputum': 66, ' muscle_pain': 67, ' muscle_wasting': 68, ' muscle_weakness': 69, ' nausea': 70, ' neck_pain': 71, ' nodal_skin_eruptions': 72, ' obesity': 73, ' pain_behind_the_eyes': 74, ' pain_during_bowel_movements': 75, ' pain_in_anal_region': 76, ' painful_walking': 77, ' palpitations': 78, ' passage_of_gases': 79, ' patches_in_throat': 80, ' phlegm': 81, ' polyuria': 82, ' prominent_veins_on_calf': 83, ' puffy_face_and_eyes': 84, ' pus_filled_pimples': 85, ' receiving_blood_transfusion': 86, ' receiving_unsterile_injections': 87, ' red_sore_around_nose': 88, ' red_spots_over_body': 89, ' redness_of_eyes': 90, ' restlessness': 91, ' runny_nose': 92, ' rusty_sputum': 93, ' scurring': 94, ' shivering': 95, ' silver_like_dusting': 96, ' sinus_pressure': 97, ' skin_peeling': 98, ' skin_rash': 99, ' slurred_speech': 100, ' small_dents_in_nails': 101, ' spinning_movements': 102, ' spotting urination': 103, ' stiff_neck': 104, ' stomach_bleeding': 105, ' stomach_pain': 106, ' sunken_eyes': 107, ' sweating': 108, ' swelled_lymph_nodes': 109, ' swelling_joints': 110, ' swelling_of_stomach': 111, ' swollen_blood_vessels': 112, ' swollen_extremeties': 113, ' swollen_legs': 114, ' throat_irritation': 115, ' toxic_look_(typhos)': 116, ' ulcers_on_tongue': 117, ' unsteadiness': 118, ' visual_disturbances': 119, ' vomiting': 120, ' watering_from_eyes': 121, ' weakness_in_limbs': 122, ' weakness_of_one_body_side': 123, ' weight_gain': 124, ' weight_loss': 125, ' yellow_crust_ooze': 126, ' yellow_urine': 127, ' yellowing_of_eyes': 128, ' yellowish_skin': 129, '(vertigo) Paroymsal  Positional Vertigo': 130, 'AIDS': 131, 'Acne': 132, 'Alcoholic hepatitis': 133, 'Allergy': 134, 'Arthritis': 135, 'Bronchial Asthma': 136, 'Cervical spondylosis': 137, 'Chicken pox': 138, 'Chronic cholestasis': 139, 'Common Cold': 140, 'Dengue': 141, 'Diabetes ': 142, 'Dimorphic hemmorhoids(piles)': 143, 'Drug Reaction': 144, 'Fungal infection': 145, 'GERD': 146, 'Gastroenteritis': 147, 'Heart attack': 148, 'Hepatitis B': 149, 'Hepatitis C': 150, 'Hepatitis D': 151, 'Hepatitis E': 152, 'Hypertension ': 153, 'Hyperthyroidism': 154, 'Hypoglycemia': 155, 'Hypothyroidism': 156, 'Impetigo': 157, 'Jaundice': 158, 'Malaria': 159, 'Migraine': 160, 'Osteoarthristis': 161, 'Paralysis (brain hemorrhage)': 162, 'Peptic ulcer diseae': 163, 'Pneumonia': 164, 'Psoriasis': 165, 'Tuberculosis': 166, 'Typhoid': 167, 'Urinary tract infection': 168, 'Varicose veins': 169, 'hepatitis A': 170, 'itching': 171}
context_string = "\n".join([f"{key}: {value}" for key, value in context.items()])

def generate_reccomendation(user_text):
    prompt = f"""
    You are given the following symptoms and predicted diseases:
    {user_text}
    
    return the type/types of doctors that would be the most beneficial in this case, could be 1-3 types depending on how broad the symptoms are
    
    i want you to return the following in json: 
    every symptom, every predicted disease, and type of doctor, no explanation needed, strictly in json"
    """

    response = model.generate_content(prompt)
    json_match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)

    if json_match:
        json_text = json_match.group(0)  # Extract matched JSON content
        try:
            cleaned_json = json.loads(json_text)  # Validate and parse JSON
            json_string = json.dumps(cleaned_json)  # Convert back to JSON string
        except json.JSONDecodeError:
            json_string = None  # Handle invalid JSON case
    else:
        json_string = None  # No JSON found
    
    return json_string


# Initialize Model
input_size = len(symptom_indexes)
num_classes = len(disease_indexes)
classifier = SymptomClassifier(input_size, num_classes)

# Load model weights
classifier.load_state_dict(torch.load("bhsoda.pth"))
classifier.eval()

# Function to predict disease from symptoms
def predict_disease(symptom_indexes_list, top_k=3):
    # Create symptom vector
    input_vector = np.zeros(len(symptom_indexes))  # Initialize all symptoms as 0
    associated_symptoms = []  # Store actual symptom names

    for idx in symptom_indexes_list:
        if 0 <= idx < len(symptom_indexes):  # Ensure the index is valid
            input_vector[idx] = 1
            symptom_name = list(symptom_indexes.keys())[list(symptom_indexes.values()).index(idx)]
            associated_symptoms.append(symptom_name)
        else:
            print(f"Warning: Symptom index '{idx}' is out of range.")

    # Convert to tensor
    input_tensor = torch.Tensor(input_vector).unsqueeze(0)  # Add batch dimension
    
    # Make prediction
    with torch.no_grad():
        output = classifier(input_tensor)  # Get raw logits
        probabilities = torch.softmax(output, dim=-1)  # Convert logits to probabilities
        top_probs, top_indices = torch.topk(probabilities, top_k, dim=-1)  # Get top-k predictions
    
    # Extract top-k predictions
    top_probs = top_probs.squeeze().tolist()  # Convert tensor to list
    top_indices = top_indices.squeeze().tolist()  # Convert tensor to list

    # Map indices to disease names
    top_diseases = [(list(disease_indexes.keys())[list(disease_indexes.values()).index(idx)], prob * 100) 
                    for idx, prob in zip(top_indices, top_probs)]

    # Print the associated symptoms
    '''
    print("Symptoms Associated with Input:")
    for symptom in associated_symptoms:
        print(f"- {symptom}")

    print("\nTop Predicted Diseases:")
    for disease, prob in top_diseases:
        print(f"{disease}")
    '''
    
    finalstring = str(associated_symptoms) + "\n" + str(top_diseases)
    reccomendation = generate_reccomendation(finalstring)
    return reccomendation




import google.generativeai as genai

# Configure Gemini with a working model
genai.configure(api_key="AIzaSyASjCwVvZUCK6WdC03nQm-1pM8aSAy5WCo")
model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

print("✅ Gemini model configured: gemini-2.0-flash-exp")

context = {' abdominal_pain': 0, ' abnormal_menstruation': 1, ' acidity': 2, ' acute_liver_failure': 3, ' altered_sensorium': 4, ' anxiety': 5, ' back_pain': 6, ' belly_pain': 7, ' blackheads': 8, ' bladder_discomfort': 9, ' blister': 10, ' blood_in_sputum': 11, ' bloody_stool': 12, ' blurred_and_distorted_vision': 13, ' breathlessness': 14, ' brittle_nails': 15, ' bruising': 16, ' burning_micturition': 17, ' chest_pain': 18, ' chills': 19, ' cold_hands_and_feets': 20, ' coma': 21, ' congestion': 22, ' constipation': 23, ' continuous_feel_of_urine': 24, ' continuous_sneezing': 25, ' cough': 26, ' cramps': 27, ' dark_urine': 28, ' dehydration': 29, ' depression': 30, ' diarrhoea': 31, ' dischromic patches': 32, ' distention_of_abdomen': 33, ' dizziness': 34, ' drying_and_tingling_lips': 35, ' enlarged_thyroid': 36, ' excessive_hunger': 37, ' extra_marital_contacts': 38, ' family_history': 39, ' fast_heart_rate': 40, ' fatigue': 41, ' fluid_overload': 42, ' foul_smell_of urine': 43, ' headache': 44, ' high_fever': 45, ' hip_joint_pain': 46, ' history_of_alcohol_consumption': 47, ' increased_appetite': 48, ' indigestion': 49, ' inflammatory_nails': 50, ' internal_itching': 51, ' irregular_sugar_level': 52, ' irritability': 53, ' irritation_in_anus': 54, ' joint_pain': 55, ' knee_pain': 56, ' lack_of_concentration': 57, ' lethargy': 58, ' loss_of_appetite': 59, ' loss_of_balance': 60, ' loss_of_smell': 61, ' malaise': 62, ' mild_fever': 63, ' mood_swings': 64, ' movement_stiffness': 65, ' mucoid_sputum': 66, ' muscle_pain': 67, ' muscle_wasting': 68, ' muscle_weakness': 69, ' nausea': 70, ' neck_pain': 71, ' nodal_skin_eruptions': 72, ' obesity': 73, ' pain_behind_the_eyes': 74, ' pain_during_bowel_movements': 75, ' pain_in_anal_region': 76, ' painful_walking': 77, ' palpitations': 78, ' passage_of_gases': 79, ' patches_in_throat': 80, ' phlegm': 81, ' polyuria': 82, ' prominent_veins_on_calf': 83, ' puffy_face_and_eyes': 84, ' pus_filled_pimples': 85, ' receiving_blood_transfusion': 86, ' receiving_unsterile_injections': 87, ' red_sore_around_nose': 88, ' red_spots_over_body': 89, ' redness_of_eyes': 90, ' restlessness': 91, ' runny_nose': 92, ' rusty_sputum': 93, ' scurring': 94, ' shivering': 95, ' silver_like_dusting': 96, ' sinus_pressure': 97, ' skin_peeling': 98, ' skin_rash': 99, ' slurred_speech': 100, ' small_dents_in_nails': 101, ' spinning_movements': 102, ' spotting urination': 103, ' stiff_neck': 104, ' stomach_bleeding': 105, ' stomach_pain': 106, ' sunken_eyes': 107, ' sweating': 108, ' swelled_lymph_nodes': 109, ' swelling_joints': 110, ' swelling_of_stomach': 111, ' swollen_blood_vessels': 112, ' swollen_extremeties': 113, ' swollen_legs': 114, ' throat_irritation': 115, ' toxic_look_(typhos)': 116, ' ulcers_on_tongue': 117, ' unsteadiness': 118, ' visual_disturbances': 119, ' vomiting': 120, ' watering_from_eyes': 121, ' weakness_in_limbs': 122, ' weakness_of_one_body_side': 123, ' weight_gain': 124, ' weight_loss': 125, ' yellow_crust_ooze': 126, ' yellow_urine': 127, ' yellowing_of_eyes': 128, ' yellowish_skin': 129, '(vertigo) Paroymsal  Positional Vertigo': 130, 'AIDS': 131, 'Acne': 132, 'Alcoholic hepatitis': 133, 'Allergy': 134, 'Arthritis': 135, 'Bronchial Asthma': 136, 'Cervical spondylosis': 137, 'Chicken pox': 138, 'Chronic cholestasis': 139, 'Common Cold': 140, 'Dengue': 141, 'Diabetes ': 142, 'Dimorphic hemmorhoids(piles)': 143, 'Drug Reaction': 144, 'Fungal infection': 145, 'GERD': 146, 'Gastroenteritis': 147, 'Heart attack': 148, 'Hepatitis B': 149, 'Hepatitis C': 150, 'Hepatitis D': 151, 'Hepatitis E': 152, 'Hypertension ': 153, 'Hyperthyroidism': 154, 'Hypoglycemia': 155, 'Hypothyroidism': 156, 'Impetigo': 157, 'Jaundice': 158, 'Malaria': 159, 'Migraine': 160, 'Osteoarthristis': 161, 'Paralysis (brain hemorrhage)': 162, 'Peptic ulcer diseae': 163, 'Pneumonia': 164, 'Psoriasis': 165, 'Tuberculosis': 166, 'Typhoid': 167, 'Urinary tract infection': 168, 'Varicose veins': 169, 'hepatitis A': 170, 'itching': 171}
context_string = "\n".join([f"{key}: {value}" for key, value in context.items()])

def generate_symptoms(user_text):
    prompt = f"""
    You are given the following symptom dictionary:
    {context_string}
    
    The user will describe their symptoms. Your task is to return a Python list containing only the key numbers of the symptoms that match the user's input.
    
    Respond *ONLY* with a valid Python list of numbers and nothing else.

    User input: "{user_text}"
    """

    response = model.generate_content(prompt)

    try:
        key_numbers = ast.literal_eval(response.text.strip())
        if isinstance(key_numbers, list) and all(isinstance(i, int) for i in key_numbers):
            return key_numbers
    except (SyntaxError, ValueError):
        return []

# # Example input
# user_input = "i have acidity, stomach pain and im tired all the time"
# symptom_keys = generate_symptoms(user_input)
# final_output = predict_disease(symptom_keys)
# print(final_output)


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import ast

# Assuming you already imported your model and context_string
# And imported generate_symptoms, predict_disease

@csrf_exempt
def predict_disease_api(request):
    print("🔍 predict_disease_api called")  # Debug
    if request.method == "POST":
        try:
            print("✅ Received POST request")
            
            # Check if we can read the request body
            body = request.body.decode('utf-8')
            print(f"📦 Raw request body: {body}")
            
            data = json.loads(body)
            user_text = data.get("complaint", "")
            print(f"✅ User complaint: '{user_text}'")

            if not user_text:
                print("❌ No complaint text provided")
                return JsonResponse({"error": "No complaint text provided."}, status=400)

            print("🔄 Calling generate_symptoms...")
            symptom_keys = generate_symptoms(user_text)
            print(f"✅ Generated symptom keys: {symptom_keys}")

            if not symptom_keys:
                print("❌ No symptoms generated")
                return JsonResponse({"error": "No valid symptoms identified from the description."}, status=400)

            print("🔄 Calling predict_disease...")
            predicted_condition = predict_disease(symptom_keys)
            print(f"✅ Prediction result: {predicted_condition}")

            return JsonResponse({
                "predicted_condition": predicted_condition,
                "symptom_keys": symptom_keys,
                "status": "success"
            })

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            print("🔍 Full traceback:")
            traceback.print_exc()
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    print("❌ Invalid method")
    return JsonResponse({"error": "Invalid request method. Only POST allowed."}, status=405)