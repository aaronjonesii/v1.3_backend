from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from nose.tools import assert_true, assert_equal
from ..models import Task
import pytest

from ...routing import application


TEST_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

@database_sync_to_async
def create_user(
        *,
        username='userone',
        password='password',
):
    user = get_user_model().objects.create_user(username=username, password=password)

    # user_group, _ = Group.objects.get_or_create(name=group)
    # user.groups.add(user_group)
    user.save()
    return user


async def auth_connect(user):
    client = Client()
    client.force_login(user=user)
    communicator = WebsocketCommunicator(
        application=application,
        path='/ct/',
        headers=[(b'cookie', f'sessionid={client.cookies["sessionid"].value}'.encode('ascii'))]
    )
    connected, _ = await communicator.connect()
    assert_true(connected)
    return communicator


async def connect_and_create_task(
        *,
        user,
        title='Test Task One',
        description='This is to test the creation of a task.',
        tags='["test", "TDD"]'):

    communicator = await auth_connect(user)
    await communicator.send_json_to({
        'type': 'create.task',
        'data': {
            'title': title,
            'description': description,
            'tags': tags,
            'owner': user.id
        }
    })
    return communicator


@database_sync_to_async
def create_task(**kwargs):
    return Task.objects.create(**kwargs)


async def connect_and_update_task(*, user, task, status):
    communicator = await auth_connect(user)
    await communicator.send_json_to({
        'type': 'update.task',
        'data': {
            'id': task.id,
            'ident': task.ident,
            'title': 'UPDATED: ' + task.title,
            'description': task.description,
            'tags': task.tags,
            'status': status,
            'owner': user.id,
        }
    })
    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebsockets:

    async def test_authorized_user_can_connect(self, settings):
        # Use in-memory channel layers for testing.
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user = await create_user(username='userone')
        communicator = await auth_connect(user)
        await communicator.disconnect()

    async def test_user_can_create_tasks(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user = await create_user(username='userone')
        communicator = await connect_and_create_task(user=user)
        # Receive JSON message from server
        response = await communicator.receive_json_from()
        data = response.get('data')
        # Confirm Data
        assert_equal('Test Task One', data['title'])
        assert_equal('This is to test the creation of a task.', data['description'])
        assert_equal('["test", "TDD"]', data['tags'])
        assert_equal('userone', data['owner']['username'])

        await communicator.disconnect()

    async def test_user_can_update_tasks(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user = await create_user(username='userone')
        task = await create_task(
            title='Test Task One',
            description='This is to test the creation of a task.',
            tags="['test', 'TDD']"
        )
        communicator = await connect_and_update_task(user=user, task=task, status=Task.IN_PROGRESS)
        response = await communicator.receive_json_from()
        data = response.get('data')
        # Confirm Data
        assert_equal(task.ident, data['ident'])
        assert_equal('UPDATED: Test Task One', data['title'])
        assert_equal(Task.IN_PROGRESS, data['status'])
        assert_equal('userone', data['owner']['username'])

        await communicator.disconnect()

    async def test_user_can_create_and_view_tasks(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user = await create_user(username='userone')
        communicator = await connect_and_create_task(user=user)
        # Receive JSON message from server
        response = await communicator.receive_json_from()
        data = response.get('data')
        # assert_equal('1', data['id'])
        assert_equal('Test Task One', data['title'])

        new_task = await create_task(
            title='Test Task Two',
            description='This is to test the creation of multiple tasks, it should return both tasks after creation.',
            tags="['test', 'TDD']"
        )
        await communicator.send_json_to({
            'type': 'create.task',
            'data': {
                'title': new_task.title,
                'description': new_task.description,
                'tags': new_task.tags,
                'owner': user.id
            }
        })
        await communicator.send_json_to({
            'type': 'view.tasks'
        })
        new_response = await communicator.receive_json_from()
        new_data = new_response.get('data')
        # TODO: Showing three tasks!!! (ERROR)
        await communicator.disconnect()


    # async def test_user_is_added_to_user_group_on_create(self, settings):
    #     settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
    #
    #     user = await create_user(username='userone', group='user')
    #
    #     # Connect and send JSON message to server.
    #     communicator = await connect_and_create_task(user=user)
    #
    #     # Receive JSON message from server.
    #     # Rider should be added to new trip's group.
    #     response = await communicator.receive_json_from()
    #     data = response.get('data')
    #
    #     task_ident = data['ident']
    #     message = {
    #         'type': 'echo.message',
    #         'data': 'This is a test message.'
    #     }
    #
    #     # Send JSON message to new trip's group.
    #     channel_layer = get_channel_layer()
    #     await channel_layer.group_send(task_ident, message=message)
    #
    #     # Receive JSON message from server.
    #     response = await communicator.receive_json_from()
    #
    #     # Confirm data.
    #     assert_equal(message, response)
    #
    #     await communicator.disconnect()

    # async def test_user_is_added_to_user_groups_on_connect(self, settings):
    #     settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
    #
    #     user = await create_user(username='userone', group='user')
    #
    #     # Create trips and link to rider.
    #     task = await create_task(
    #         title='Test Task One',
    #         description='This is to test the creation of a task.',
    #         tags="['test', 'TDD']",
    #         user=user
    #     )
    #
    #     # Connect to server.
    #     # Trips for rider should be retrieved.
    #     # Rider should be added to trips' groups.
    #     communicator = await auth_connect(user)
    #
    #     message = {
    #         'type': 'echo.message',
    #         'data': 'This is a test message.'
    #     }
    #
    #     channel_layer = get_channel_layer()
    #
    #     # Test sending JSON message to trip group.
    #     await channel_layer.group_send(task.ident, message=message)
    #     response = await communicator.receive_json_from()
    #     assert_equal(message, response)
    #
    #     await communicator.disconnect()

    # async def test_admin_can_update_tasks(self, settings):
    #     settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
    #
    #     task = await create_task(
    #         title='Test Task One',
    #         description='This is to test the creation of a task.',
    #         tags="['test', 'TDD']"
    #     )
    #     user = await create_user(
    #         username='adminone',
    #         group='admin'
    #     )
    #
    #     # Send JSON message to server.
    #     communicator = await connect_and_update_task(
    #         user=user,
    #         task=task,
    #         status=Task.IN_PROGRESS
    #     )
    #
    #     # Receive JSON message from server.
    #     response = await communicator.receive_json_from()
    #     data = response.get('data')
    #
    #     # Confirm data.
    #     assert_equal(task.id, data['id'])
    #     assert_equal(task.ident, data['ident'])
    #     assert_equal('Test Task One', data['title'])
    #     assert_equal('This is to test the creation of a task.', data['description'])
    #     assert_equal("['test', 'TDD']", data['tags'])
    #     assert_equal(Task.IN_PROGRESS, data['status'])
    #     assert_equal(user.username, data['admin'].get('username'))
    #     assert_equal(None, data['user'])
    #
    #     await communicator.disconnect()
