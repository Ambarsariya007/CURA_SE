# Create a new file called list_models.py in your Django project root
import google.generativeai as genai
import os

# Configure with your API key
genai.configure(api_key="AIzaSyASjCwVvZUCK6WdC03nQm-1pM8aSAy5WCo")

print("🔍 Available Gemini Models:")
print("=" * 50)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Supported methods: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"❌ Error listing models: {e}")