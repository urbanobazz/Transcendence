import json, html
from channels.generic.websocket import AsyncWebsocketConsumer
from .online_users import add_online_user, remove_online_user, get_online_users
from .umc_connection import create_multi, validate_user, get_blocklist


class ChatRoomConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["query_string"].decode().split("username=")[-1]
        self.room_name = "main_chat_room"
        self.room_group_name = f"chat_{self.room_name}"
        self.blocklist = get_blocklist(self.user)

        await self.channel_layer.group_add(self.room_group_name,
                                           self.channel_name)

        await self.channel_layer.group_add(f"user_{self.user}",
                                           self.channel_name)

        await self.accept()

        add_online_user(self.user)

        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "chat_message",
                "message": f"{self.user} joined the chat",
                "user": "PongChat",
            })
        await self.broadcast_online_users()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name,
                                               self.channel_name)

        await self.channel_layer.group_discard(f"user_{self.user}",
                                               self.channel_name)

        remove_online_user(self.user)

        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "chat_message",
                "message": f"{self.user} left the chat",
                "user": "PongChat",
            })

        await self.broadcast_online_users()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")
        print(f"message {message}")
        if message.startswith("/"):
            await self.handle_command(message)
        else:
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "chat_message",
                "message": message,
                "user": self.user,
            })

    async def handle_dm(self, message):
        parts = message.split(" ", 2)
        if len(parts) < 3:
            await self.send(text_data=json.dumps({
                "message": "Invalid /dm command. Usage: /dm USERNAME MESSAGE",
                "user": "PongChat",
            }))
            return

        receiver, dm_message = parts[1], parts[2]
        online_users = get_online_users(self.blocklist)
        sanitized_dm_message = html.escape(dm_message)

        if receiver in online_users:
            await self.channel_layer.group_send(
                f"user_{receiver}",
                {
                    "type": "chat_message",
                    "message":
                    f"({self.user} -> you) {sanitized_dm_message}",  # don't touch this message or blocklist logic will break
                    "user": "PongChat",
                })
            return f"(you -> {receiver}) {sanitized_dm_message}"
        else:
            return f"User {receiver} is not online.",

    async def broadcast_online_users(self):
        online_users_list = get_online_users(self.blocklist)
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "online_users_update",
            "online_users": online_users_list,
        })

    async def online_users_update(self, event):
        online_users = event["online_users"]
        await self.send(text_data=json.dumps({
            "message": f"Online Users: {', '.join(online_users)}",
            "user": "PongChat",
        }))

    async def chat_message(self, event):
        message = event["message"]
        user = event["user"]
        sender = ''
        if user == "PongChat":
            if " challenged you: Join" in message:
                sender = message.split(" challenged you: Join")[0]
            elif " -> you) " in message:
                sender = message.split(" -> you) ")[0][1:]

        if user in self.blocklist or sender in self.blocklist:
            return

        await self.send(text_data=json.dumps({
            "message": message,
            "user": user
        }))

    async def invite_player(self, message):
        target_user = message.split(" ", 1)[1].strip()
        if target_user not in get_online_users(self.blocklist):
            return f'{target_user} is not online.'
        game_id = create_multi(self.user, target_user)
        join_link = f'<a href="#" class="chatbutton" id="join-game-{game_id}">join here</a>'

        await self.channel_layer.group_send(
            f"user_{target_user}",
            {
                "type": "chat_message",
                "message":
                f"{self.user} challenged you: Join {join_link}",  # don't touch this message or blocklist logic will break
                "user": "PongChat"
            })
        return f"Invite sent to {target_user} and the game is ready: {join_link}!"

    async def get_info(self, message):
        target_user = message.split(" ", 1)[1].strip()
        if not message.endswith(target_user):
            return "Unclear instructions, expected: /info USERNAME"
        if target_user not in get_online_users(self.blocklist):
            return f'{target_user} is not online.'
        target_id = validate_user(target_user)
        info_link = f'<a class="chatbutton" href="/profile/{target_id}" id="profile-{target_id}" data-link>{target_user}\'s profile</a>'
        return f"Click here to see {info_link}"

    async def handle_command(self, message):
        if message.startswith("/dm "):
            response = await self.handle_dm(message)
        elif message == "/online":
            online_users_list = get_online_users(self.blocklist)
            response = f"Currently online: {', '.join(online_users_list)}"
        elif message.startswith("/invite "):
            response = await self.invite_player(message)
        elif message.startswith("/info "):
            response = await self.get_info(message)
        elif message == "/play":
            response = "The AI opponent is waiting: <a class='chatbutton' href='/single-player'>play Now</a>"
        else:
            response = ("Available chat options:\n"
                        "/online - list all users currently logged in"
                        "/info USERNAME - View a user profile\n"
                        "/invite USERNAME - Invite a user to a new game\n"
                        "/dm USERNAME MESSAGE - Send a direct message\n"
                        "/play - Play against an AI opponent\n"
                        "/help - Display this message")
        await self.send(text_data=json.dumps({
            "message": response,
            "user": "PongChat"
        }))
