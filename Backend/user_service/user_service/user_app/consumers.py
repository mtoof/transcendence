import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class PersonalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        my_id = self.scope['user'].id
        other_user_id = self.scope['url_route']['kwargs']['id']
        if int(my_id) > int(other_user_id):
            self.room_name = f'{my_id}-{other_user_id}'
        else:
            self.room_name = f'{other_user_id}-{my_id}'

        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data: str = "", bytes_data=None):
        data = json.loads(text_data)
        print(data)
        message = data['message']
        username = data['username']
        receiver = data['receiver']

        await self.save_message(username, self.room_group_name, message, receiver)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

    async def disconnect(self, code):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def save_message(self, username, thread_name, message, receiver):
        from .models import ChatModel, ChatNotification
        from django.contrib.auth.models import User

        chat_obj = ChatModel.objects.create(
            sender=username, message=message, thread_name=thread_name)
        other_user_id = self.scope['url_route']['kwargs']['id']
        get_user = User.objects.get(id=other_user_id)
        if receiver == get_user.username:
            ChatNotification.objects.create(chat=chat_obj, user=get_user)

@method_decorator(csrf_exempt, name='dispatch')
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        my_id = self.scope['user'].id
        self.room_group_name = f'{my_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        data = json.loads(event.get('value'))
        count = data['count']
        print(count)
        await self.send(text_data=json.dumps({
            'count':count
        }))

@method_decorator(csrf_exempt, name='dispatch')
class OnlineStatusConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        token = self.get_token_from_query_string()
        self.scope['user'] = await self.get_user_from_token(token)
        self.room_group_name = 'online_status'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.change_online_status(self.scope['user'], 'open')
        # print(f'Connected to WebSocket: {self.room_group_name}')

    def get_token_from_query_string(self):
        query_string = self.scope['query_string'].decode()
        params = dict(param.split('=') for param in query_string.split('&'))
        return params.get('token')

    @database_sync_to_async
    def get_user_from_token(self, token):
        from django.contrib.auth.models import AnonymousUser
        from .models import UserProfileModel
        from rest_framework_simplejwt.tokens import AccessToken, TokenError 
        from rest_framework_simplejwt.exceptions import InvalidToken
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return UserProfileModel.objects.get(id=user_id)
        except (UserProfileModel.DoesNotExist, TokenError, InvalidToken):
            return AnonymousUser()
    
    async def receive(self, text_data: str = "", bytes_data=None):
        # print(f'Received message: {text_data}')
        try:
            data = json.loads(text_data)
            username = data['username']
            connection_type = data['type']
            # print(f'Parsed data: {data}')
            if connection_type == 'close':
                await self.close()
            await self.change_online_status(username, connection_type)


        except json.JSONDecodeError as e:
            # print(f'JSON decode error: {e}')
            await self.close(code=4001)
        except KeyError as e:
            # print(f'Missing key: {e}')
            await self.close(code=4002)
        except Exception as e:
            # print(f'Error in receive: {e}')
            await self.close(code=1011)

    async def send_onlineStatus(self, event):
        try:
            data = json.loads(event.get('value'))
            username = data['username']
            online_status = data['status']
            print(f'Sending status: {data}')
            await self.send(text_data=json.dumps({
                'username': username,
                'online_status': online_status
            }))
        except json.JSONDecodeError as e:
            print(f'JSON decode error in send_onlineStatus: {e}')
        except KeyError as e:
            print(f'Missing key in send_onlineStatus: {e}')
        except Exception as e:
            print(f'Error in send_onlineStatus: {e}')

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.change_online_status(self.scope['user'], 'close')
        # print(f'Disconnected from WebSocket: {self.room_group_name} with code: {code}')

    @database_sync_to_async
    def change_online_status(self, username, c_type):
        from .models import UserProfileModel as User

        try:
            userprofile = User.objects.get(username=username)
            # print(f'User profile username: {userprofile.username}')
            if c_type == 'open':
                userprofile.online_status = True
                userprofile.save()
            else:
                userprofile.online_status = False
                userprofile.save()
            # print(f'Changed status for {username} to {c_type}')
        except User.DoesNotExist:
            print(f'User {username} does not exist.')
        except User.DoesNotExist:
            print(f'User profile for {username} does not exist.')
        except Exception as e:
            print(f'Error changing status: {e}')
