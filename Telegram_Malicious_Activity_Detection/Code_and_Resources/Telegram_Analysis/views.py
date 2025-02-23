from telethon.sync import TelegramClient
from telethon.tl.types import PeerChat
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import errors
import json
from pymongo import MongoClient
import base64
from .forms import MessageForm
from django.shortcuts import render
import pymongo
from bson import ObjectId
from datetime import datetime
import os
import joblib

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

                me = await telethon_client.get_me()
                group_input_entity = group_link
                entity = PeerChat(int(group_input_entity)) if group_input_entity.isdigit() else group_input_entity
                group = await telethon_client.get_entity(entity)

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
                            sender_username = "Unknown"
                            sender_id = message.sender_id if hasattr(message, "sender_id") else "Unknown"

                            if sender_id != "Unknown":
                                try:
                                    sender = await telethon_client.get_entity(sender_id)
                                    sender_username = sender.username if hasattr(sender,
                                                                                 "username") else sender.first_name
                                except:
                                    sender_username = "Unknown"
                            message_dict = {
                                "id": message.id,
                                "sender_id": message.sender_id if hasattr(message, "sender_id") else "Unknown",
                                "sender_username": sender_username,
                                "date": message.date,
                                "message": message.message,
                            }
                            category = model1.predict([message.message])[0]
                            message_dict["category"] = category
                            all_messages.append(message_dict)
                    offset_id = messages[-1].id

                group_title = group.title if hasattr(group, "title") else "UnnamedGroup"
                filename = f"{group_title}_messages.json"
                collection_name = group_title
                new_collection_name = group_title

                with open(filename, "w") as outfile:
                    json.dump(all_messages, outfile, cls=DateTimeEncoder)

                collection = db[collection_name]
                collection.delete_many({})  # Clear existing data before inserting new
                collection.insert_many(all_messages)

                print(f"Data inserted into MongoDB collection: {collection_name}")

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
        db_names = client.list_database_names()
        target_collection_name = new_collection_name
        target_db_name = None

        for db_name in db_names:
            db = client[db_name]
            collections = db.list_collection_names()
            if target_collection_name in collections:
                target_db_name = db_name
                break

        if not target_db_name:
            target_db_name = target_collection_name
            db = client[target_db_name]
            collection = db[target_collection_name]

        db = client[target_db_name]
        collection = db[target_collection_name]
        query = {"category": selected_category}
        projection = {
            "_id": 0, "id": 1, "sender_id": 1, "sender_username": 1, "date": 1, "message": 1, "category": 1
        }
        results = collection.find(query, projection)
        matching_documents = []

        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
            if "date" in result and isinstance(result["date"], datetime):
                result["date"] = result["date"].strftime("%Y-%m-%d %H:%M:%S")
            matching_documents.append(result)

        client.close()
        return render(request, "chart.html", {"matching_documents": matching_documents})

    return render(request, "chart.html")
