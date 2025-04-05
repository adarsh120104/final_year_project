# from telethon.sync import TelegramClient
# from telethon.tl.types import PeerChat
# from telethon import TelegramClient
# from telethon.tl.functions.messages import GetHistoryRequest
# from telethon import errors
# import json
# from pymongo import MongoClient
# import base64
# from .forms import MessageForm
# from django.shortcuts import render
# import pymongo
# from bson import ObjectId
# from datetime import datetime
# import os
# import joblib
# import requests
#
# # Load the model
# model1 = joblib.load(os.path.dirname(__file__) + "\\bestSVCModel.pkl")
#
# mongo_client = MongoClient("mongodb://localhost:27017/")
# db = mongo_client["telegramDB"]
#
# class DateTimeEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, datetime):
#             return o.isoformat()
#         if isinstance(o, bytes):
#             return base64.b64encode(o).decode("utf-8")
#         return super().default(o)
#
# new_collection_name = None
#
# async def message_form(request):
#     global new_collection_name
#     if request.method == "POST":
#         form = MessageForm(request.POST)
#         if form.is_valid():
#             group_link = form.cleaned_data["group_link"]
#
#             api_id = 24878087
#             api_hash = "588890997e609d49050223ec030605ca"
#             phone = "+91 8754181880"
#             username = "adarsh"
#
#             async def main(phone):
#                 global new_collection_name
#                 telethon_client = TelegramClient(username, api_id, api_hash)
#                 await telethon_client.start()
#
#                 if not await telethon_client.is_user_authorized():
#                     await telethon_client.send_code_request(phone)
#                     try:
#                         await telethon_client.sign_in(phone, input("Enter the code: "))
#                     except errors.SessionPasswordNeededError:
#                         await telethon_client.sign_in(password=input("Password: "))
#
#                 group = await telethon_client.get_entity(group_link)
#                 offset_id = 0
#                 limit = 1000
#                 all_messages = []
#
#                 while True:
#                     history = await telethon_client(GetHistoryRequest(
#                         peer=group,
#                         offset_id=offset_id,
#                         offset_date=None,
#                         add_offset=0,
#                         limit=limit,
#                         max_id=0,
#                         min_id=0,
#                         hash=0,
#                     ))
#                     if not history.messages:
#                         break
#
#                     messages = history.messages
#                     for message in messages:
#                         if message.message:
#                             message_dict = {
#                                 "id": message.id,
#                                 "sender_id": message.sender_id if hasattr(message, "sender_id") else "Unknown",
#                                 "sender_username": "Unknown",
#                                 "date": message.date,
#                                 "message": message.message,
#                             }
#                             category = model1.predict([message.message])[0]
#
#                             # Second verification using Hugging Face API
#                             API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
#                             headers = {"Authorization": "Bearer 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"}
#                             categories = [
#                                 "hacking and cybercrime",
#                                 "internet discussions",
#                                 "movie piracy and illegal streaming",
#                                 "normal conversation",
#                                 "violence"
#                             ]
#
#                             response = requests.post(
#                                 API_URL,
#                                 headers=headers,
#                                 json={"inputs": message.message, "parameters": {"candidate_labels": categories}}
#                             )
#                             hf_category = response.json().get("labels", ["Unknown"])[0]
#
#                             message_dict["category"] = category
#                             message_dict["hf_category"] = hf_category
#                             all_messages.append(message_dict)
#
#                     offset_id = messages[-1].id
#
#                 new_collection_name = group.title
#                 collection = db[new_collection_name]
#                 collection.delete_many({})
#                 collection.insert_many(all_messages)
#
#                 await telethon_client.disconnect()
#                 return render(request, "chart.html", {"group_link": group_link})
#
#             result = await main(phone)
#             return result
#     else:
#         form = MessageForm()
#     return render(request, "message_form.html", {"form": form})
#
# def chart(request):
#     global new_collection_name
#     client = pymongo.MongoClient("mongodb://localhost:27017/")
#
#     if request.method == "POST":
#         selected_category = request.POST.get("category")
#         collection = db[new_collection_name]
#
#         query = {"$or": [
#             {"category": selected_category},
#             {"hf_category": selected_category}
#         ]}
#         projection = {"_id": 0, "id": 1, "sender_id": 1, "sender_username": 1, "date": 1, "message": 1, "category": 1, "hf_category": 1}
#
#         results = list(collection.find(query, projection))
#         client.close()
#         return render(request, "chart.html", {"matching_documents": results})
#
#     return render(request, "chart.html")
#
#
# # chanegs
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import errors
import json
from pymongo import MongoClient
import base64
from .forms import MessageForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
import pymongo
from bson import ObjectId
from datetime import datetime
import os
import joblib
import requests
from twilio.rest import Client

# Twilio credentials (Replace with your own)
TWILIO_ACCOUNT_SID = "AC8bbc0328c7ede30ea5713472520c6faa"
TWILIO_AUTH_TOKEN = "97789b4e3690f09dd75887abec021187"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox number
ADMIN_WHATSAPP_NUMBER = "whatsapp:+918754181880"  # Your WhatsApp number

# Load the model
model1 = joblib.load(os.path.dirname(__file__) + "\\bestSVCModel.pkl")

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["telegramDB"]

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, bytes):
            return base64.b64encode(o).decode("utf-8")
        return super().default(o)

new_collection_name = None

async def message_form(request):
    global new_collection_name
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            group_link = form.cleaned_data["group_link"]

            api_id = 24878087
            api_hash = "588890997e609d49050223ec030605ca"
            phone = "+91 8754181880"
            username = "adarsh"

            async def main(phone):
                global new_collection_name
                telethon_client = TelegramClient(username, api_id, api_hash)
                await telethon_client.start()

                if not await telethon_client.is_user_authorized():
                    await telethon_client.send_code_request(phone)
                    try:
                        await telethon_client.sign_in(phone, input("Enter the code: "))
                    except errors.SessionPasswordNeededError:
                        await telethon_client.sign_in(password=input("Password: "))

                group = await telethon_client.get_entity(group_link)
                offset_id = 0
                limit = 1000
                all_messages = []

                while True:
                    history = await telethon_client(GetHistoryRequest(
                        peer=group,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0,
                    ))
                    if not history.messages:
                        break

                    messages = history.messages
                    for message in messages:
                        if message.message:
                            if hasattr(message, "sender_id") and message.sender_id:
                                try:
                                    sender = await telethon_client.get_entity(message.sender_id)
                                    sender_username = sender.username if sender.username else "No Username"
                                except Exception as e:
                                    sender_username = "Unknown"
                            else:
                                sender_username = "Unknown"
                            message_dict = {
                                "id": message.id,
                                "sender_id": message.sender_id if hasattr(message, "sender_id") else "Unknown",
                                "sender_username": sender_username,
                                "date": message.date,
                                "message": message.message,
                            }
                            category = model1.predict([message.message])[0]

                            # Second verification using Hugging Face API
                            API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
                            headers = {"Authorization": "Bearer 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"}
                            categories = [
                                "hacking and cybercrime",
                                "internet discussions",
                                "movie piracy and illegal streaming",
                                "normal conversation",
                                "violence"
                            ]

                            response = requests.post(
                                API_URL,
                                headers=headers,
                                json={"inputs": message.message, "parameters": {"candidate_labels": categories}}
                            )
                            hf_category = response.json().get("labels", ["Unknown"])[0]

                            message_dict["category"] = category
                            message_dict["hf_category"] = hf_category
                            all_messages.append(message_dict)

                    offset_id = messages[-1].id

                new_collection_name = group.title
                collection = db[new_collection_name]
                collection.delete_many({})
                collection.insert_many(all_messages)

                await telethon_client.disconnect()
                return render(request, "chart.html", {"group_link": group_link})

            result = await main(phone)
            return result
    else:
        form = MessageForm()
    return render(request, "message_form.html", {"form": form})

def chart(request):
    global new_collection_name
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    if request.method == "POST":
        selected_category = request.POST.get("category")
        collection = db[new_collection_name]

        query = {"$or": [
            {"category": selected_category},
            {"hf_category": selected_category}
        ]}
        projection = {"_id": 0, "id": 1, "sender_id": 1, "sender_username": 1, "date": 1, "message": 1, "category": 1, "hf_category": 1}

        results = list(collection.find(query, projection))
        client.close()
        return render(request, "chart.html", {"matching_documents": results, "selected_category": selected_category})

    return render(request, "chart.html")

def send_report(request):
    if request.method == "POST":
        selected_messages_str = request.POST.get("selected_messages[]")  # Get the string
        if not selected_messages_str:
            return JsonResponse({"status": "error", "message": "No messages selected!"})

        selected_messages = selected_messages_str.split(",")  # Split by comma

        try:
            selected_message_ids = [int(msg_id.strip()) for msg_id in selected_messages]  # Convert to integers safely
        except ValueError as e:
            return JsonResponse({"status": "error", "message": f"Invalid message ID format: {selected_messages_str}"})

        # Fetch selected messages from the database
        collection = db[new_collection_name]
        query = {"id": {"$in": selected_message_ids}}
        projection = {"_id": 0, "sender_id": 1, "sender_username": 1, "message": 1, "category": 1, "hf_category": 1}
        messages = list(collection.find(query, projection))

        if not messages:
            return JsonResponse({"status": "error", "message": "No matching messages found!"})

        # Format message for WhatsApp
        report_text = "🚨 *Reported Messages* 🚨\n\n"
        for msg in messages:
            report_text += f"📌 *Sender ID:* {msg['sender_id']}\n"
            report_text += f"👤 *Username:* {msg['sender_username']}\n"
            report_text += f"💬 *Message:* {msg['message']}\n"
            final_category = msg.get("hf_category", msg.get("category", "Unknown"))  # Prioritize hf_category
            report_text += f"💬 *Category:* {final_category}\n"
            report_text += "--------------------------\n"

        # Send message via WhatsApp
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=report_text,
            to=ADMIN_WHATSAPP_NUMBER
        )

        return JsonResponse({"status": "success", "message": "Report sent successfully!"})

    return JsonResponse({"status": "error", "message": "Invalid request!"})

#-------------------------------------------------------------------------------------------------------------------------
# the below is code without reporting
# from telethon.sync import TelegramClient
# from telethon.tl.types import PeerChat
# from telethon import TelegramClient
# from telethon.tl.functions.messages import GetHistoryRequest
# from telethon import errors
# import json
# from pymongo import MongoClient
# import base64
# from .forms import MessageForm
# from django.shortcuts import render
# import pymongo
# from bson import ObjectId
# from datetime import datetime
# import os
# import joblib
# import requests
#
# # Load the model
# model1 = joblib.load(os.path.dirname(__file__) + "\\bestSVCModel.pkl")
#
# mongo_client = MongoClient("mongodb://localhost:27017/")
# db = mongo_client["telegramDB"]
#
# class DateTimeEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, datetime):
#             return o.isoformat()
#         if isinstance(o, bytes):
#             return base64.b64encode(o).decode("utf-8")
#         return super().default(o)
#
# new_collection_name = None
#
# async def message_form(request):
#     global new_collection_name
#     if request.method == "POST":
#         form = MessageForm(request.POST)
#         if form.is_valid():
#             group_link = form.cleaned_data["group_link"]
#
#             api_id = 24878087
#             api_hash = "588890997e609d49050223ec030605ca"
#             phone = "+91 8754181880"
#             username = "adarsh"
#
#             async def main(phone):
#                 global new_collection_name
#                 telethon_client = TelegramClient(username, api_id, api_hash)
#                 await telethon_client.start()
#
#                 if not await telethon_client.is_user_authorized():
#                     await telethon_client.send_code_request(phone)
#                     try:
#                         await telethon_client.sign_in(phone, input("Enter the code: "))
#                     except errors.SessionPasswordNeededError:
#                         await telethon_client.sign_in(password=input("Password: "))
#
#                 group = await telethon_client.get_entity(group_link)
#                 offset_id = 0
#                 limit = 1000
#                 all_messages = []
#
#                 while True:
#                     history = await telethon_client(GetHistoryRequest(
#                         peer=group,
#                         offset_id=offset_id,
#                         offset_date=None,
#                         add_offset=0,
#                         limit=limit,
#                         max_id=0,
#                         min_id=0,
#                         hash=0,
#                     ))
#                     if not history.messages:
#                         break
#
#                     messages = history.messages
#                     for message in messages:
#                         if message.message:
#                             message_dict = {
#                                 "id": message.id,
#                                 "sender_id": message.sender_id if hasattr(message, "sender_id") else "Unknown",
#                                 "sender_username": "Unknown",
#                                 "date": message.date,
#                                 "message": message.message,
#                             }
#                             category = model1.predict([message.message])[0]
#
#                             # Second verification using Hugging Face API
#                             API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
#                             headers = {"Authorization": "Bearer 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"}
#                             categories = [
#                                 "hacking and cybercrime",
#                                 "internet discussions",
#                                 "movie piracy and illegal streaming",
#                                 "normal conversation",
#                                 "violence"
#                             ]
#
#                             response = requests.post(
#                                 API_URL,
#                                 headers=headers,
#                                 json={"inputs": message.message, "parameters": {"candidate_labels": categories}}
#                             )
#                             hf_category = response.json().get("labels", ["Unknown"])[0]
#
#                             message_dict["category"] = category
#                             message_dict["hf_category"] = hf_category
#                             all_messages.append(message_dict)
#
#                     offset_id = messages[-1].id
#
#                 new_collection_name = group.title
#                 collection = db[new_collection_name]
#                 collection.delete_many({})
#                 collection.insert_many(all_messages)
#
#                 await telethon_client.disconnect()
#                 return render(request, "chart.html", {"group_link": group_link})
#
#             result = await main(phone)
#             return result
#     else:
#         form = MessageForm()
#     return render(request, "message_form.html", {"form": form})
#
# def chart(request):
#     global new_collection_name
#     client = pymongo.MongoClient("mongodb://localhost:27017/")
#
#     if request.method == "POST":
#         selected_category = request.POST.get("category")
#         collection = db[new_collection_name]
#
#         query = {"$or": [
#             {"category": selected_category},
#             {"hf_category": selected_category}
#         ]}
#         projection = {"_id": 0, "id": 1, "sender_id": 1, "sender_username": 1, "date": 1, "message": 1, "category": 1, "hf_category": 1}
#
#         results = list(collection.find(query, projection))
#         client.close()
#         return render(request, "chart.html", {"matching_documents": results})
#
#     return render(request, "chart.html")


# chanegss

