import os
import json
import sqlite3
import requests
import asyncio
import uvicorn

API_TOKEN = '7199311260:AAFMIt_JVhe_7n1G_Y8gadolx6KOxgKEAkw'
WEBHOOK_URL = f"https://e5d6-185-139-139-204.ngrok-free.app/webhook/"  # Server URL ni o'zgartirisj


conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)''')
conn.commit()

def get_users():
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    return [user[0] for user in users]


async def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    headers = {'Content-Type': 'application/json'}
    await asyncio.to_thread(requests.post, url, data=json.dumps(payload), headers=headers)

async def send_message_users(chats_id, text):
    for chat_id in chats_id:
        await send_message(chat_id, text)

async def handle_update(update):
    if "message" in update and "text" in update["message"]:
        message = update["message"]
        user_id = message["from"]["id"]
        text = message["text"]

        if text == "/start":
            cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
            conn.commit()
            await send_message(user_id, f"Xush kelibsi! ")


async def polling():
    offset = 0
    while True:
        url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates"
        params = {'offset': offset, 'timeout': 100}
        response = await asyncio.to_thread(requests.get, url, params=params)
        response_json = response.json()

        if response_json.get("result"):
            for update in response_json["result"]:
                offset = update["update_id"] + 1
                await handle_update(update)


async def app(scope, receive, send):
    assert scope['type'] == 'http'

    if scope['path'] == '/send/' and scope['method'] == 'POST':
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            print(message)
            body += message.get('body', b'')
            more_body = message.get('more_body', False)

        data = json.loads(body)

        message = data['message']

        chat_ids = get_users()

        await send_message_users(chat_ids, message)
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"status":"ok"}',
        })



    if scope['path'] == '/webhook/' and scope['method'] == 'POST':
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)

        update = json.loads(body)
        await handle_update(update)

        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"status":"ok"}',
        })
    else:
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [
                [b'content-type', b'text/plain'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Not found',
        })


if __name__ == "__main__":
    mode = os.getenv('MODE', 'webhook')
    if mode == 'webhook':
        requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}")
        uvicorn.run("app:app", host="0.0.0.0", port=8000)
    else:
        requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")
        asyncio.run(polling())
