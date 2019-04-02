from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APIClient, APITestCase
from django.test import RequestFactory

from ..serializers import TaskSerializer, UserSerializer
from ..models import Task
from  ..views import TaskView

USERNAME = 'testuser'
PASSWORD = 'pAssw0rd!'


def create_user(username=USERNAME, password=PASSWORD):
    return get_user_model().objects.create_user(
        username=username, password=password)


class AuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_sign_up(self):
        response = self.client.post(reverse('signup'), data={
            'username': USERNAME,
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        user = get_user_model().objects.last()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response.data['id'], user.id)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['first_name'], user.first_name)
        self.assertEqual(response.data['last_name'], user.last_name)
        self.assertEqual(response.data['email'], user.email)

    def test_user_can_log_in(self):
        user = create_user()
        response = self.client.post(reverse('login'), data={
            'username': USERNAME,
            'password': PASSWORD
        })
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data['username'], user.username)

    def test_user_can_log_out(self):
        user = create_user()
        self.client.login(username=user.username, password=PASSWORD)
        response = self.client.post(reverse('logout'))
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)


# class HttpTaskTest(APITestCase):
#
#     def setUp(self):
#         # user = create_user()
#         # self.client = APIClient()
#         # self.client.login(username=user.username, password=PASSWORD)
#         self.factory = RequestFactory()
#         self.user = create_user()
#
#     def test_user_can_list_tasks(self):
#         request = self.factory.get(reverse_lazy('api:task_list'))
#         request.user = self.user
#         tasks = [
#             Task.objects.create(title="Test Task One", description="Testing to make sure a user can see their tasks", tags=['test', 'TDD']),
#             Task.objects.create(title="Test Task Two", description="Making sure there is no problem with more than one task", tags=['test', 'TDD'])
#         ]
#         # response = self.client.get(reverse_lazy('api:task_list'))
#         response = TaskView.as_view({'get': 'list'})(request)
#         print(response.data)
#         print(request.user)
#         self.assertEqual(status.HTTP_200_OK, response.status_code)
#         exp_task_idents = [task.ident for task in tasks]
#         print('E',exp_task_idents)
#         act_task_idents = [task.get('ident') for task in response.data['results']]
#         print('A',act_task_idents)
#
#         self.assertCountEqual(exp_task_idents, act_task_idents)
#
#     def test_user_can_retrieve_task_by_ident(self):
#         task = Task.objects.create(title="Test Task Three", description="Testing a single detail view of a task", tags=['test', 'TDD'])
#         response = self.client.get(task.get_absolute_url())
#         self.assertEqual(status.HTTP_200_OK, response.status_code)
#         self.assertEqual(task.ident, response.data.get('ident'))
