from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Conversation, Message, Profile
from .forms import messageForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from datetime import datetime
import json
import os
import requests
from django.conf import settings

# Create your views here.

def chatApp(request, convId):
    conversations = Conversation.objects.filter(
        Q(first_user=request.user.id) | Q(other_user=request.user.id)
    )
    activeConversation = Conversation.objects.get(id=convId)

    other = (
        activeConversation.other_user
        if activeConversation.first_user == request.user
        else activeConversation.first_user
    )
    otherProfile = Profile.objects.filter(user=other).first()

    bot = User.objects.filter(username="ChatBot").first()
    botConv = conversations.filter(other_user=bot).first()
    current_time = datetime.now()

    return render(
        request,
        "chat/index.html",
        {
            "otherProfile": otherProfile,
            "conversations": conversations,
            "activeConversation": activeConversation,
            "botConv": botConv,
            "server_timestamp": current_time,
        },
    )

def emptyChat(request):
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    userProfile = Profile.objects.filter(user=request.user).first()
    conversations = Conversation.objects.filter(
        Q(first_user=request.user.id) | Q(other_user=request.user.id)
    )
    bot = User.objects.filter(username="ChatBot").first()
    if bot is None:
        bot = User(username="ChatBot", password="ChatBot")
        bot.save()
    botConv = conversations.filter(other_user=bot).first()
    if botConv is None:
        botConv = Conversation(first_user=request.user, other_user=bot)
        botConv.save()

    return render(
        request,
        "chat/empty-chat.html",
        {
            "userProfile": userProfile,
            "conversations": conversations,
            "botConv": botConv,
        },
    )

def gptTranslate(message, language):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=PUT YOU API KEY HERE"

    prompt = f"""listen Gemini, you have to translate the given text in this {language}, for example 'hello ab', write ab as is and translate the rest, no explanation, just translate. Do not translate names. Here's the text: {message}"""

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(url, json=data)
    result = response.json()

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return "Translation failed."

@csrf_exempt
@require_POST
def chatbot(request):
    try:
        user_data = json.loads(request.body)
        user_message = user_data.get("userMessage", "Default User Message")

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=PUT YOU API KEY HERE"
        data = {
            "contents": [{"parts": [{"text": user_message}]}]
        }

        response = requests.post(url, json=data)
        result = response.json()
        response_message = result["candidates"][0]["content"]["parts"][0]["text"]

        return JsonResponse({"status": "success", "generatedText": response_message})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def newChat(request):
    conversations = Conversation.objects.filter(
        Q(first_user=request.user.id) | Q(other_user=request.user.id)
    )
    bot = User.objects.filter(username="ChatBot").first()
    botConv = conversations.filter(other_user=bot).first()
    errors = []

    if request.method == "POST":
        username = request.POST["username"]
        new_user = User.objects.filter(username=username).first()
        if not new_user:
            errors.append("User not found. Invalid Username.")
        else:
            current_convs = request.user.my_conversations.all()
            other_convs = request.user.other_conversations.all()
            all_convs = list(current_convs) + list(other_convs)
            for conv in all_convs:
                if (conv.first_user == new_user) or (conv.other_user == new_user):
                    errors.append("Chat with the user already exists")
                    break
            else:
                new_conv = Conversation(first_user=request.user, other_user=new_user)
                new_conv.save()
                return redirect("chat:chatApp", convId=new_conv.id)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    return render(
        request,
        "chat/new-chat.html",
        {
            "errors": errors,
            "conversations": conversations,
            "botConv": botConv,
        },
    )

def cropImage(request, convId):
    conversations = Conversation.objects.filter(
        Q(first_user=request.user.id) | Q(other_user=request.user.id)
    )
    activeConversation = Conversation.objects.get(id=convId)
    current_time = datetime.now()

    return render(
        request,
        "chat/crop-image.html",
        {
            "conversations": conversations,
            "activeConversation": activeConversation,
            "server_timestamp": current_time,
        },
    )

@csrf_exempt
def saveImage(request):
    if request.method == "POST" and request.FILES.get("uploaded-image"):
        uploaded_file = request.FILES["uploaded-image"]
        file_path = os.path.join(
            settings.MEDIA_ROOT, "uploaded_images", uploaded_file.name
        )
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "uploaded_images"), exist_ok=True)
        with open(file_path, "wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return JsonResponse({"status": "success", "message": "Image uploaded successfully."})

    return JsonResponse({"status": "error", "message": "No file received."})

@csrf_exempt
def saveChatbotMessage(request):
    if request.method == "POST":
        otherID = request.POST["otherID"]
        convID = request.POST["convID"]
        message = request.POST["message"]

        if otherID and convID and message:
            bot = User.objects.get(id=otherID)
            conv = Conversation.objects.get(id=convID)
            newMessage = Message(conversation=conv, content=message, created_by=bot)
            newMessage.save()
            conv.save()
            return JsonResponse({"status": "success", "message": "Message saved successfully."})

    return JsonResponse({"status": "error", "message": "Message not saved."})

@csrf_exempt
def getUpdatedConversations(request):
    updated_conversations = Conversation.objects.all().values(
        "id", "first_user", "other_user", "modified_at"
    )
    updated_conversations_list = list(updated_conversations)
    return JsonResponse(updated_conversations_list, safe=False)

@csrf_exempt
def translate_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message_content = data.get("messageContent", "")
            language = data.get("language", "")
            translation = gptTranslate(message_content, language)
            return JsonResponse({"translatedMessage": translation})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
