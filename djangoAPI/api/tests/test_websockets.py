from django.contrib.auth import get_user_model
from django.test import Client
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework.authtoken.models import Token
from nose.tools import assert_true, assert_equal
from ..models import Task
import pytest
import json

from ...routing import application


TEST_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# TODO: Create User
@database_sync_to_async
def create_user(*, username='userone', password='password'):
    user = get_user_model().objects.create_user(
        username=username,
        password=password
    )
    user.save()
    return user


async def auth_connect(user):
    client = Client()
    user_token = Token.objects.get_or_create(user=user)[0]
    client.force_login(user=user)
    communicator = WebsocketCommunicator(
        application=application,
        path='/ws/tasks/',
        headers=[
            ("Content-Type", "text/plain"),
            ("Authorization", f"Token {user_token}"),
            (b'cookie', f'sessionid={client.cookies["sessionid"].value}'.encode('ascii')),
        ]
    )
    connected, _ = await communicator.connect()
    assert_true(connected)
    return communicator


async def create_task(user, comm, title='Test Task One', description='Description of Task One', tags='["test", "TDD"]'):
    comm_task = {
        'type': 'create.task',
        'data': {
            'title': title,
            'description': description,
            'tags': tags,
            # 'owner': user.id
        }
    }
    await comm.send_json_to(comm_task)
    return comm


async def update_task(user, comm, task, status):
    user_token = Token.objects.get_or_create(user=user)[0]
    user_id = Token.objects.filter(key__contains=user_token).values()[0]['user_id']
    updated_task = {
        'type': 'update.task',
        'data': {
            # 'id': task['id'],
            'ident': task['ident'],
            'title': 'UPDATED: ' + task['title'],
            'description': task['description'],
            'tags': task['tags'],
            'status': status,
            'owner': user_id,
        }
    }
    await comm.send_json_to(updated_task)
    return comm


async def get_all_tasks(comm):
    await comm.send_json_to({'type': 'view.tasks'})
    response = await comm.receive_json_from()
    tasks = json.loads(response.get('data'))
    return tasks


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebsockets:
    # async def test_authroized_user_can_connect(self, settings):
    #     settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
    #     user = await create_user(username='userone')
    #     comm = await auth_connect(user)
    #     print('\n Successfully Created User: ', user)
    #     await comm.disconnect()

    async def test_user_can_create_tasks(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user = await create_user(username='userone')
        comm = await auth_connect(user)
        print('\n Successfully Created User: ', user)

        # User One Task One
        await create_task(user, comm, title='Test Task One')
        response = await comm.receive_json_from()
        data = json.loads(response.get('data'))[0]['fields']
        assert_equal('Test Task One', data['title'])
        assert_equal(user.id, data.get('owner'))
        print('\n Successfully Created First Task: ', data)

        # User One Task Two
        await create_task(user, comm, title='Test Task Two', description='Description fo Task Two')
        response = await comm.receive_json_from()
        data = json.loads(response.get('data'))[1]['fields']
        assert_equal('Test Task Two', data['title'])
        assert_equal(user.id, data.get('owner'))
        print('\n Successfully Created Second Task: ', data)

        # User One All Tasks
        tasks = await get_all_tasks(comm)
        print(f"\n User: {user} has the following {len(tasks)} tasks: {tasks}")

        # DISCONNECT
        await comm.disconnect()

        # User Two Task One
        user2 = await create_user(username='usertwo')
        comm = await auth_connect(user2)
        print('\n Successfully Created User: ', user2)
        await create_task(user2, comm, title='User Number Two Test Task')
        response = await comm.receive_json_from()
        data = json.loads(response.get('data'))[0]['fields']
        assert_equal('User Number Two Test Task', data['title'])
        assert_equal(user2.id, data.get('owner'))
        print('\n Successfully Created User Two First Task: ', data)

        # User Two All Tasks
        tasks = await get_all_tasks(comm)
        print(f"\n User: {user2} has the following {len(tasks)} tasks: {tasks}")

        # DISCONNECT
        await comm.disconnect()

        # User One Task Three
        comm = await auth_connect(user)
        await create_task(user, comm, title='Test Task Three', description='Description of Test Task Three after reconnecting')
        response = await comm.receive_json_from()
        data = json.loads(response.get('data'))[2]['fields']
        assert_equal('Test Task Three', data['title'])
        assert_equal(user.id, data.get('owner'))
        print('\n Successfully Created Task Three after re-connecting: ', data)

        # User One All Tasks
        tasks = await get_all_tasks(comm)
        print(f"\n User: {user} has the following {len(tasks)} tasks: {tasks}")

        # DISCONNECT
        await comm.disconnect()

    async def test_user_can_update_tasks(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user = await create_user(username='userone')
        comm = await auth_connect(user)

        # Create Task
        await create_task(user, comm, title='Task to test updates')
        response = await comm.receive_json_from()
        task = json.loads(response.get('data'))[0]['fields']
        assert_equal('Task to test updates', task['title'])
        assert_equal(user.id, task['owner'])
        print(f"\n User: {user} created the following tasks: {task}")

        # Update Task
        await update_task(user, comm, task, status=Task.IN_PROGRESS)
        response = await comm.receive_json_from()
        task = json.loads(response.get('data'))[0]['fields']
        assert_equal(Task.IN_PROGRESS, task['status'])
        assert_equal('UPDATED: Task to test updates', task['title'])
        print(f"\n User: {user} Updated the following tasks: {task}")

        # DISCONNECT
        await comm.disconnect()
