# working code with two models stored locally,sending all kind of reports including emojis

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import errors
import json
from pymongo import MongoClient
import base64
from .forms import MessageForm
from django.shortcuts import render
from django.http import JsonResponse
import pymongo
from datetime import datetime, timedelta
from twilio.rest import Client
from django.utils import timezone
# Import transformers for local models
from transformers import pipeline

# Initialize local models
bart_classifier = pipeline("zero-shot-classification", model="E:\\final_year_project\\final_year_project\\Telegram_Malicious_Activity_Detection\\Code_and_Resources\\Telegram_Analysis\\models\\bart-large-mnli")
roberta_classifier = pipeline("zero-shot-classification", model="E:\\final_year_project\\final_year_project\\Telegram_Malicious_Activity_Detection\\Code_and_Resources\\Telegram_Analysis\\models\\roberta-large")

# Twilio
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_WHATSAPP_NUMBER = "whatsapp:+"
ADMIN_WHATSAPP_NUMBER = "whatsapp:+"


# model1 = joblib.load(os.path.dirname(__file__) + "\\bestSVCModel.pkl")

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

            api_id = 
            api_hash = ""
            phone = "+91 "
            username = ""

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

                three_months_ago = timezone.now() - timedelta(days=90)

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
                        if message.date < three_months_ago:
                            continue

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

                            # category = model1.predict([message.message])[0]
                            categories = [
                                "cybercrime",
                                "movie piracy and illegal streaming",
                                "normal chat",
                                "hate speech or violence",
                                "technical discussion",
                                "mental health crisis or suicidal thoughts"
                            ]

                            bart_result = bart_classifier(message.message, categories)
                            bart_scores = bart_result["scores"]
                            bart_labels = bart_result["labels"]
                            bart_category = bart_labels[0]
                            bart_max_score = bart_scores[0]

                            roberta_result = roberta_classifier(message.message, categories)
                            roberta_scores = roberta_result["scores"]
                            roberta_labels = roberta_result["labels"]
                            roberta_category = roberta_labels[0]
                            roberta_max_score = roberta_scores[0]

                            if bart_max_score > roberta_max_score:
                                best_category = bart_category
                                best_score = bart_max_score
                            else:
                                best_category = roberta_category
                                best_score = roberta_max_score

                            message_dict["roberta_category"] = roberta_category
                            message_dict["roberta_scores"] = roberta_max_score
                            message_dict["bart_category"] = bart_category
                            message_dict["bart_scores"] = bart_max_score
                            message_dict["best_category"] = best_category
                            message_dict["best_score"] = best_score

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
    collection = db[new_collection_name]

    if request.method == "POST":
        selected_category = request.POST.get("category")
        time_filter = request.POST.get("time_filter")

        query = {
            "$or": [
                {"category": selected_category},
                {"best_category": selected_category}
            ]
        }

        if time_filter:
            now = datetime.now()
            if time_filter == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query["date"] = {"$gte": start}
            elif time_filter == "yesterday":
                start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
                query["date"] = {"$gte": start, "$lt": end}
            elif time_filter == "last_week":
                start = now - timedelta(days=7)
                query["date"] = {"$gte": start}
            elif time_filter == "one_month":
                start = now - timedelta(days=30)
                query["date"] = {"$gte": start}
            elif time_filter == "three_months":
                start = now - timedelta(days=90)
                query["date"] = {"$gte": start}

        projection = {"_id": 0, "id": 1, "sender_id": 1, "sender_username": 1, "date": 1, "message": 1, "category": 1, "best_category": 1}
        results = list(collection.find(query, projection))
        client.close()

        return render(request, "chart.html", {
            "matching_documents": results,
            "selected_category": selected_category
        })

    return render(request, "chart.html")


def send_report(request):
    if request.method == "POST":
        selected_messages_str = request.POST.get("selected_messages[]")
        if not selected_messages_str:
            return JsonResponse({"status": "error", "message": "No messages selected!"})

        selected_messages = selected_messages_str.split(",")

        try:
            selected_message_ids = [int(msg_id.strip()) for msg_id in selected_messages]
        except ValueError as e:
            return JsonResponse({"status": "error", "message": f"Invalid message ID format: {selected_messages_str}"})

        collection = db[new_collection_name]
        query = {"id": {"$in": selected_message_ids}}
        projection = {"_id": 0, "sender_id": 1, "sender_username": 1, "message": 1, "category": 1, "best_category": 1}
        messages = list(collection.find(query, projection))

        if not messages:
            return JsonResponse({"status": "error", "message": "No matching messages found!"})

        report_text = "🚨 *Reported Messages* 🚨\n\n"
        for msg in messages:
            report_text += f"📌 *Sender ID:* {msg['sender_id']}\n"
            report_text += f"👤 *Username:* {msg['sender_username']}\n"
            report_text += f"💬 *Message:* {msg['message']}\n"
            final_category = msg.get("best_category", msg.get("category", "Unknown"))
            report_text += f"💬 *Category:* {final_category}\n"
            report_text += "--------------------------\n"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=report_text,
            to=ADMIN_WHATSAPP_NUMBER
        )

        return JsonResponse({"status": "success", "message": "Report sent successfully!"})

    return JsonResponse({"status": "error", "message": "Invalid request!"})
