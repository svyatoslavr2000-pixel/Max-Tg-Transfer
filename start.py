import asyncio
import json
import websockets
from aiogram import Bot
from aiogram.enums import ParseMode

# Конфигурация
TELEGRAM_BOT_TOKEN = "8422372599:AAE7bsc8AOmTPNL6iZbIS1TJzMwTO8PVuEM"     # Токен бота Telegram
TELEGRAM_CHAT_ID = "-1002990915733"       # ID группы Telegram, например: -1001234567890
MAX_TOKEN = "An_Sx6HQ9HDihGbutQjIGH5F8tejvkc1FjD6xqKYkA-4l5QRjSlY5RptvtqTfehKcNxNuJs8P1ZPzaa9at7tqQuPBhGKY-UxbySDmqMTv5RAAIEhiWdN0G_ZNRNlSivs4lu5dRtmatrsMG3OAYRYLgKirqo0VhyaUCP8z2_5Djqh4XEhuJbGYCU7p8jM5Hjoi1g9QJrb0rhgIoQkxVIUOvuiI4QcAdjz6cmfXBfYO6-PPInhlsRI8BDsWOrj1jdWc-oQyMq6dqHoDKLfSO4F24jGA7fctaCCKZkyn2xP2bE_QUOrJifVNDELBS8dMS4MLHJTdydV21EbAX_vwr-vJDowPIe_LOjJthSA4H5egWd3GauVX_e8JBATvWirUBNLq6H_oRJIXiMXfTkvV2p41I1FG9DYgJ1iFZ1Uu3mYmkrS4ZkSeMcmf-M6Q4L_YYb1UaKTYd4OiSy2BwjhqRMz9cZOmwNpd2LtX6OZII4y2gswDw4GX6AhAVU0sMA2SgBWrq8RWBeMQ2scT01MtaqlaMq0XejwB5kOtbqxFJQwSVYeo7ULylR2jv3WACLwlKaqQTzUfhsslJW7OvArARJXIxVmKZj48ONCeuBv3u7ZFQOhd8r2zewyjIzdZ_cHoqvQht4MbWA4uQCJbwua10MuACTzJQejF3iQMw-w0qa0B4leDEnd-4dL92QVncYrD2H0LL8n6qw"              # Токен аккаунта Max

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)

async def send_to_telegram(text: str):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)

async def get_user_name(websocket, sender_id):
    request = {
        "ver": 11, "cmd": 0, "seq": 2, "opcode": 32,
        "payload": {"contactIds": [sender_id]}
    }
    await websocket.send(json.dumps(request))
    response = await websocket.recv()
    data = json.loads(response)
    if data.get("opcode") == 32 and data.get("payload", {}).get("contacts"):
        for contact in data["payload"]["contacts"]:
            if str(contact.get("id")) == str(sender_id):
                return contact.get("names", [{}])[0].get("name", sender_id)
    return sender_id

async def connect_to_max(maxtoken):
    uri = "wss://ws-api.oneme.ru/websocket"
    async with websockets.connect(uri) as websocket:
        # Авторизация
        first_message = {
            "ver": 11,
            "cmd": 0,
            "seq": 2,
            "opcode": 6,
            "payload": {
                "userAgent": {
                    "deviceType": "WEB",
                    "locale": "ru",
                    "deviceLocale": "en",
                    "osVersion": "ResendLinux",
                    "deviceName": "Firefox",
                    "headerUserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
                    "appVersion": "25.7.11",
                    "screen": "827x1323 1.9x",
                    "timezone": "Europe/Moscow"
                },
                "deviceId": "d4a88e2a-dc04-48ca-b918-6fd91ddf392d"
            }
        }
        await websocket.send(json.dumps(first_message))
        response = await websocket.recv()
        print(f"Ответ на авторизацию: {response}")

        # Вход с токеном
        second_message = {
            "ver": 11,
            "cmd": 0,
            "seq": 3,
            "opcode": 19,
            "payload": {
                "interactive": False,
                "token": maxtoken,
                "chatsSync": 0,
                "contactsSync": 0,
                "presenceSync": 0,
                "draftsSync": 0,
                "chatsCount": 40
            }
        }
        await websocket.send(json.dumps(second_message))

        groups = {}

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data["opcode"] == 19:
                    # Список групп
                    for chat in data["payload"].get("chats", []):
                        if chat.get("type") == "CHAT":
                            groups[str(chat["id"])] = chat.get("title", str(chat["id"]))
                    print("Группы обновлены:", groups)

                elif data["opcode"] == 64:
                    # ЛС
                    sender = str(data["payload"]["message"]["sender"])
                    text = data["payload"]["message"].get("text", "")
                    sender_name = await get_user_name(websocket, sender)
                    await send_to_telegram(
                        f"({sender})
Было получено новое личное сообщение от <b>{sender_name}</b>, его текст:

<code>{text}</code>"
                    )

                elif data["opcode"] == 128:
                    # Сообщение в группе
                    chat_id = str(data["payload"]["chatId"])
                    sender = str(data["payload"]["message"]["sender"])
                    text = data["payload"]["message"].get("text", "")
                    chat_name = groups.get(chat_id, chat_id)
                    sender_name = await get_user_name(websocket, sender)
                    await send_to_telegram(
                        f"({chat_id}, {sender})
Было получено новое сообщение из группы <b>{chat_name}</b> от <b>{sender_name}</b>, его текст:

<code>{text}</code>"
                    )

            except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")

async def main():
    try:
        await connect_to_max(MAX_TOKEN)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
