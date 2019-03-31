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

        # Keep track of the user's trips.
        self.tasks = set()

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            # Get trips and add rider to each one's group.
            channel_groups = []
            # print(self.scope)
            self.tasks = set(await self._get_tasks(self.scope['user']))
            # for task in self.tasks:
            #     channel_groups.append(self.channel_layer.group_add(task, self.channel_name))
            # asyncio.gather(*channel_groups)
            await self.accept()

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        if message_type == 'create.task':
            await self.test_task(content)
        elif message_type == 'update.task':
            await self.update_task(content)
        elif message_type == 'view.tasks':
            await self.view_tasks()

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
        task_data = ReadOnlyTaskSerializer(task).data

        # Handle add only if trip is not being tracked
        if task.ident not in self.tasks:
            self.tasks.add(task.ident)
            await self.channel_layer.group_add(group=task.ident, channel=self.channel_name)

        await self.send_json({
            'type': 'MESSAGE',
            'data': task_data
        })

    async def update_task(self, event):
        task = await self._update_task(event.get('data'))
        task_data = ReadOnlyTaskSerializer(task).data

        # Handle add only if trip is not being tracked.
        # This happens when a driver accepts a request.
        # if task.ident not in self.tasks:
        #     self.tasks.add(task.ident)
        #     await self.channel_layer.group_add(
        #         group=task.ident,
        #         channel=self.channel_name
        #     )

        await self.send_json({
            'type': 'MESSAGE',
            'data': task_data
        })

    async def view_tasks(self):
        tasks = await self._return_tasks(self.scope['user'])
        await self.send_json({
            'type': 'MESSAGE',
            'data': tasks
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
    def _create_task(self, user_id, task):
        task['owner'] = self.scope['user'].pk
        print('Task data before creation in consumer: ', task)
        serializer = TaskSerializer(data=task)
        serializer.is_valid(raise_exception=True)
        print('Serializer validated data: ', serializer.validated_data)
        task = serializer.create(serializer.validated_data)
        print('Task after creation in consumer: ', task.owner_id, task)
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
        print('Task before update in consumers: ',content)
        instance = Task.objects.get(ident=content.get('ident'))
        serializer = TaskSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        task = serializer.update(instance, serializer.validated_data)
        return task


    @database_sync_to_async
    def _return_tasks(self, user):
        if not user.is_authenticated:
            raise Exception('User is not authenticated.')
        queryset = user.tasks_as_owner.all()
        tasks = serializers.serialize('json', queryset)
        return tasks