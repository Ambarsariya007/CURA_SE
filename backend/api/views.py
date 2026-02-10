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

# =========================
# DJANGO + DRF IMPORTS
# =========================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth import get_user_model, logout
from django.middleware.csrf import get_token
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import CustomUser, ConsultationReport

# =========================
# STANDARD LIBS
# =========================
import json
import os
import ast
import re
import logging

# =========================
# ML (RANDOM FOREST ONLY)
# =========================
import joblib
import numpy as np

# =========================
# GEMINI
# =========================
from google import genai
import os


API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not found")

client = genai.Client(api_key=API_KEY)


# =========================
# LOAD RF MODEL FILES
# =========================
from django.conf import settings
import os
import joblib
from django.conf import settings
import os
import joblib

MODEL_DIR = os.path.join(settings.BASE_DIR, "ML_MODEL")

rf_model = joblib.load(os.path.join(MODEL_DIR, "rf_symptom_disease.pkl"))
tfidf = joblib.load(os.path.join(MODEL_DIR, "tfidf.pkl"))
label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.pkl"))
# =========================
# SYMPTOM CONTEXT (TEXT)
# =========================
symptom_context = [
    "headache", "high fever", "fatigue", "nausea", "vomiting",
    "cough", "chest pain", "abdominal pain", "diarrhoea",
    "joint pain", "breathlessness", "dizziness",
    "loss of appetite", "mild fever", "muscle pain",
    "throat irritation", "runny nose", "skin rash", "itching"
]

context_string = ", ".join(symptom_context)

# =========================
# GEMINI → EXTRACT SYMPTOMS
# =========================
def generate_symptoms(user_text):
    text = user_text.lower()
    extracted = []

    for symptom in symptom_context:
        words = symptom.replace("_", " ").split()
        if any(word in text for word in words):
            extracted.append(symptom)

    return list(set(extracted))


# =========================
# RANDOM FOREST PREDICTION
# =========================
def predict_disease(symptoms, top_k=3):
    text_input = " ".join(symptoms)
    X = tfidf.transform([text_input])

    probs = rf_model.predict_proba(X)[0]
    top_indices = np.argsort(probs)[-top_k:][::-1]

    diseases = [
        {
            "disease": label_encoder.inverse_transform([i])[0],
            "confidence": round(probs[i] * 100, 2)
        }
        for i in top_indices
    ]

    payload = {
        "symptoms": symptoms,
        "predicted_diseases": [d["disease"] for d in diseases]
    }

    payload["doctor_recommendation"] = generate_recommendation(payload)
    return payload

# =========================
# GEMINI → DOCTOR RECOMMEND
# =========================
def generate_recommendation(payload):
    diseases = payload.get("predicted_diseases", [])

    doctor_map = {
        "Typhoid": ["General Physician"],
        "Dengue": ["General Physician"],
        "Malaria": ["General Physician"],
        "Pneumonia": ["Pulmonologist"],
        "Common Cold": ["General Physician"],
        "Gastroenteritis": ["Gastroenterologist"],
        "Urinary tract infection": ["Urologist"],
        "Migraine": ["Neurologist"],
        "Diabetes ": ["Endocrinologist"],
        "Hypertension ": ["Cardiologist"],
    }

    doctors = set()

    for disease in diseases:
        for key in doctor_map:
            if key.lower() in disease.lower():
                doctors.update(doctor_map[key])

    if not doctors:
        doctors.add("General Physician")

    return list(doctors)

# =========================
# API: PREDICT DISEASE
# =========================
@csrf_exempt
@csrf_exempt
def predict_disease_api(request):
    print("🚀 predict_disease_api HIT")

    try:
        print("📦 RAW BODY:", request.body)

        data = json.loads(request.body)
        complaint = data.get("complaint", "")

        print("🧠 Complaint:", complaint)

        symptoms = generate_symptoms(complaint)
        print("🩺 Extracted symptoms:", symptoms, type(symptoms))

        if not symptoms:
            return JsonResponse({"error": "No symptoms detected"}, status=400)

        prediction = predict_disease(symptoms)
        print("📊 Prediction:", prediction)

        return JsonResponse({
            "status": "success",
            "symptoms": symptoms,
            "prediction": prediction
        })

    except Exception as e:
        import traceback
        print("💥 ERROR:")
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# =========================
# AUTH VIEWS
# =========================
User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Registration successful"}, status=201)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("🔥 LOGIN PAYLOAD:", request.data)

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            print("❌ LOGIN ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
            }
        })


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logged out"})

def csrf_token_view(request):
    return JsonResponse({"csrfToken": get_token(request)})

# =========================
# SAVE CONSULTATION
# =========================
@csrf_exempt
def save_consultation(request):
    data = json.loads(request.body)
    report = ConsultationReport.objects.create(
        user_id=data.get("user_id"),
        responses=data.get("responses", {}),
        ml_result=json.dumps(data.get("mlResult"))
    )
    return JsonResponse({"report_id": report.id}, status=201)



def generate_pdf(request, report_id):
    try:
        # ============================
        # FETCH REPORT
        # ============================
        report = ConsultationReport.objects.get(id=report_id)
        print(f"🔍 ML Result raw data: {report.ml_result}")
        print(f"🔍 ML Result type: {type(report.ml_result)}")

        # ============================
        # SAFE ML RESULT PARSE
        # ============================
        ml_raw = report.ml_result
        ml_data = {}

        try:
            # First decode
            if isinstance(ml_raw, str):
                ml_data = json.loads(ml_raw)

                # 🔥 SECOND decode if still string
                if isinstance(ml_data, str):
                    ml_data = json.loads(ml_data)

            elif isinstance(ml_raw, dict):
                ml_data = ml_raw

        except Exception as e:
            print("❌ ML JSON decode failed:", e)
            ml_data = {}

        # ✅ NOW THIS WILL WORK
        predicted_diseases = ml_data.get("predicted_diseases", [])

        # Final safety check
        if not isinstance(ml_data, dict):
            ml_data = {}

        predicted_diseases = ml_data.get("predicted_diseases", [])    

        # ============================
        # HTTP RESPONSE
        # ============================
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="consultation_report_{report_id}.pdf"'

        # ============================
        # COLORS & DOCUMENT
        # ============================
        primary_color = colors.HexColor('#1E88E5')
        secondary_color = colors.HexColor('#43A047')
        text_color = colors.HexColor('#212121')
        light_bg = colors.HexColor('#F5F5F5')

        doc = SimpleDocTemplate(
            response,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch
        )

        elements = []
        styles = getSampleStyleSheet()

        # ============================
        # STYLES
        # ============================
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=primary_color,
            spaceAfter=16,
            alignment=1
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=secondary_color,
            spaceAfter=12
        )

        section_title = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=text_color,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            italic=0
        )

        body_text = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=text_color,
            leading=14
        )

        # ============================
        # HEADER
        # ============================
        elements.append(Paragraph(
            "<font color='#1E88E5'><b>CURA</b></font> <font color='#43A047'>Health Consultation</font>",
            title_style
        ))

        elements.append(Paragraph(f"Consultation Report #{report.id}", subtitle_style))

        if hasattr(report, 'created_at'):
            elements.append(Paragraph(
                f"Generated on: {report.created_at.strftime('%B %d, %Y at %H:%M')}",
                body_text
            ))

        elements.append(Spacer(1, 20))

        separator = Table([['']], colWidths=[7 * inch])
        separator.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 1, primary_color),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ]))
        elements.append(separator)
        elements.append(Spacer(1, 20))

        # ============================
        # REPORT SUMMARY
        # ============================
        elements.append(Paragraph("Report Summary", section_title))
        elements.append(Spacer(1, 6))

        top_disease_names = ", ".join(predicted_diseases) if predicted_diseases else "N/A"

        summary_table = Table([
            [Paragraph("<b>Report ID:</b>", body_text), Paragraph(str(report.id), body_text)],
            [Paragraph("<b>ML Diagnosis:</b>", body_text), Paragraph(top_disease_names, body_text)],
        ], colWidths=[2 * inch, 4.5 * inch])

        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), light_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # ============================
        # USER RESPONSES
        # ============================
        if report.responses:
            elements.append(Paragraph("Consultation Responses", section_title))
            elements.append(Spacer(1, 6))

            response_data = [[
                Paragraph("<b>Question</b>", body_text),
                Paragraph("<b>Response</b>", body_text)
            ]]

            for q, a in report.responses.items():
                response_data.append([
                    Paragraph(q, body_text),
                    Paragraph(a, body_text)
                ])

            response_table = Table(response_data, colWidths=[3.25 * inch, 3.25 * inch])
            response_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))

            elements.append(response_table)
            elements.append(Spacer(1, 30))

            # =======================
        # Medical References Section
        # =======================
        elements.append(Paragraph("Medical References for Doctor", section_title))
        elements.append(Spacer(1, 8))

        medical_references = {
            'Typhoid': {'page': 269, 'notes': 'Enteric fever management'},
            'Malaria': {'page': 312, 'notes': 'Antimalarial treatment'},
            'Common Cold': {'page': 245, 'notes': 'Viral URI management'},
            'Dengue': {'page': 189, 'notes': 'Hemorrhagic fever protocol'},
            'Pneumonia': {'page': 278, 'notes': 'Community-acquired pneumonia'},
            'Gastroenteritis': {'page': 295, 'notes': 'Acute diarrhea management'},
            'Urinary tract infection': {'page': 302, 'notes': 'UTI treatment guidelines'},
        }

        # Safe ML parsing (already fixed earlier)
        predicted_diseases = ml_data.get("predicted_diseases", [])

        reference_rows = [
            [
                Paragraph("<b>Disease</b>", body_text),
                Paragraph("<b>Reference</b>", body_text),
                Paragraph("<b>Page</b>", body_text),
                Paragraph("<b>Notes</b>", body_text),
            ]
        ]

        for disease in predicted_diseases:
            if disease in medical_references:
                ref = medical_references[disease]

                book_url = "http://127.0.0.1:8000/api/medical-books/oxford_emergency_medicine.pdf"

                link = Paragraph(
                    f'<a href="{book_url}" color="blue"><u>Oxford Emergency Medicine</u></a>',
                    body_text
                )

                reference_rows.append([
                    Paragraph(disease, body_text),
                    link,
                    Paragraph(str(ref["page"]), body_text),
                    Paragraph(ref["notes"], body_text),
                ])

        if len(reference_rows) > 1:
            ref_table = Table(reference_rows, colWidths=[1.4*inch, 2.4*inch, 0.7*inch, 2.5*inch])

            ref_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),

                # Alignment
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))

            elements.append(ref_table)

        else:
            elements.append(Paragraph("No medical references available.", body_text))

        # ============================
        # DISCLAIMER
        # ============================
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "This report is computer-generated and not a substitute for professional medical advice.",
            ParagraphStyle('Disclaimer', fontSize=8, textColor=colors.grey, alignment=1)
        ))

        # ============================
        # BUILD PDF
        # ============================
        doc.build(elements)
        return response

    except ConsultationReport.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)



from django.http import FileResponse
import os
from django.conf import settings

def serve_medical_book(request, book_name):
    """Serve medical book PDF files"""
    try:
        # Security check - only allow specific books
        allowed_books = ['oxford_emergency_medicine.pdf']
        if book_name not in allowed_books:
            return HttpResponse("Book not found", status=404)
            
        # ✅ Updated path to the correct location
        book_path = os.path.join(settings.BASE_DIR, 'api', 'med_books', book_name)
        
        print(f"🔍 Looking for book at: {book_path}")
        
        if os.path.exists(book_path):
            response = FileResponse(open(book_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{book_name}"'
            return response
        else:
            return HttpResponse(f"Book file not found at: {book_path}", status=404)
            
    except Exception as e:
        return HttpResponse(f"Error serving book: {str(e)}", status=500)
    
    from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    return Response({
        "id": request.user.id,
        "email": request.user.email
    })
