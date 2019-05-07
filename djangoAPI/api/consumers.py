from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core import serializers

from .serializers import TaskSerializer, ReadOnlyTaskSerializer
from .models import Task
import asyncio

from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model


class TaskConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, scope):
        super().__init__(scope)

        self.tasks = set()

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            self.tasks = set(await self._get_tasks(self.scope['user']))
            # TODO: Check if token is valid
            await self.accept()

    async def receive_json(self, content, **kwargs):
        print('#consumers.py - Request from client => ', content)
        message_type = content.get('type')
        if message_type == 'create.task':
            await self.create_task(content)
        elif message_type == 'update.task':
            await self.update_task(content)
        elif message_type == 'view.tasks':
            await self.view_tasks()
        elif message_type == 'delete.task':
            await self.delete_task(content)

    async def echo_message(self, event):
        await self.send_json(event)

    async def test_task(self, content):
        user_token = self.scope['headers'][1][1].strip('Token ')
        if user_token:
            user_id = Token.objects.filter(key__contains=user_token).values()[0]['user_id']
            user = get_user_model().objects.get(id__contains=user_id)
            task = content.get('data')
            task = await self._create_task(user_id, task)
            task_data = ReadOnlyTaskSerializer(task).data
            await self.send_json({
                'type': 'MESSAGE',
                'data': task_data
            })

    async def create_task(self, event):
        task = await self._create_task(event.get('data'))
        task_data = ReadOnlyTaskSerializer(task).data  # Newly created task data
        tasks = await self._return_tasks(self.scope['user'])
        await self.send_json({
            'type': 'TASKS',
            'data': tasks
        })

    async def update_task(self, event):
        task = await self._update_task(event.get('data'))
        updated_task = ReadOnlyTaskSerializer(task).data
        tasks = await self._return_tasks(self.scope['user'])
        # TODO: Create response for Updated Task failure
        await self.send_json({
            'type': 'TASK_UPDATED',
            'data': tasks
        })

    async def view_tasks(self):
        tasks = await self._return_tasks(self.scope['user'])
        await self.send_json({
            'type': 'TASKS',
            'data': tasks
        })

    async def delete_task(self, event):
        try:
            delete_status = await self._delete_task(event.get('data'))
            if delete_status == 1:
                tasks = await self._return_tasks(self.scope['user'])
                await self.send_json({
                    'type': 'DELETE_CONFIRMATION',
                    'data': tasks
                })
            else: raise
        except: await self.send_json({
            'type': 'DELETE FAILED',
            'data': event.get('data')
        })

    async def disconnect(self, code):
        # Remove this channel from every trip's group.
        channel_groups = [
            self.channel_layer.group_discard(
                group=task,
                channel=self.channel_name
            )
            for task in self.tasks
        ]
        asyncio.gather(*channel_groups)

        # Remove all references to trips.
        self.tasks.clear()

        await super().disconnect(code)

    @database_sync_to_async
    def _create_task(self, task):
        task['owner'] = self.scope['user'].pk
        serializer = TaskSerializer(data=task)
        serializer.is_valid(raise_exception=True)
        task = serializer.create(serializer.validated_data)
        return task

    @database_sync_to_async
    def _get_tasks(self, user):
        if not user.is_authenticated:
            raise Exception('User is not authenticated.')
        user_groups = user.groups.values_list('name', flat=True)
        return user.tasks_as_owner.only('ident').values_list('ident', flat=True)
        # if 'user' in user_groups:
        #     return user.tasks_as_user.exclude(
        #         status=Task.COMPLETED
        #     ).only('ident').values_list('ident', flat=True)
        # else:
        #     return user.tasks_as_user.exclude(
        #         status=Task.COMPLETED
        #     ).only('ident').values_list('ident', flat=True)

    @database_sync_to_async
    def _update_task(self, content):
        instance = Task.objects.get(ident=content.get('ident'))
        serializer = TaskSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        task = serializer.update(instance, serializer.validated_data)
        return task

    @database_sync_to_async
    def _delete_task(self, content):
        try:
            instance = Task.objects.get(ident=content.get('ident'))
            serializer = TaskSerializer(data=content)
            serializer.is_valid(raise_exception=True)
            instance.delete()
            return 1
        except:
            print('Deletion fo Task failed, from _Delete_task in consumers...');
            return 0


    @database_sync_to_async
    def _return_tasks(self, user):
        if not user.is_authenticated:
            raise Exception('User is not authenticated.')
        queryset = user.tasks_as_owner.all()
        tasks = serializers.serialize('json', queryset)
        return tasks
