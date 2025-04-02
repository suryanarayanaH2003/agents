from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from .agents import run_crew
from pymongo import MongoClient
import datetime

# MongoDB Connection
client = MongoClient('mongodb+srv://suryahihub:713321Ad105@cluster0.iojbuw6.mongodb.net/')
db = client['policy_compliance_db']
policies_collection = db['policies']
results_collection = db['compliance_results']


@csrf_exempt
@api_view(['GET'])
def home(request):
    return JsonResponse({'message': 'This is home page.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def policy_compliance_view(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']

    # Ensure it's a .txt file
    if not uploaded_file.name.endswith('.txt'):
        return Response({"error": "Only .txt files are allowed"}, status=status.HTTP_400_BAD_REQUEST)

    file_path = default_storage.save(f"policies/{uploaded_file.name}", uploaded_file)

    # Read content of the text file
    with default_storage.open(file_path, 'r') as f:
        file_content = f.read()

    policy_data = {
        "file_name": uploaded_file.name,
        "file_path": file_path,
        "content": file_content,
        "uploaded_at": str(datetime.datetime.now())
    }

    policy_result = policies_collection.insert_one(policy_data)
    policy_id = str(policy_result.inserted_id)  # ✅ Convert ObjectId to string

    # Run CrewAI process
    try:
        result = run_crew(file_content, policy_id)  # Pass content instead of file path

        compliance_result = results_collection.find_one({"policy_id": policy_id})

        # ✅ Convert MongoDB ObjectId fields to strings
        if compliance_result:
            compliance_result["_id"] = str(compliance_result["_id"])
            compliance_result["policy_id"] = str(compliance_result["policy_id"])

        return Response({
            "message": "Compliance check completed",
            "policy_id": policy_id,
            "result": compliance_result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
