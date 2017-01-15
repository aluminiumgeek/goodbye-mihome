import json
import unittest
from unittest.mock import patch

from utils import Notifications


class MockRedis:
    db = {}

    @staticmethod
    def set(key, value):
        MockRedis.db[key] = value.encode()

    @staticmethod
    def get(key):
        return MockRedis.db.get(key)


class NotificationsTestCase(unittest.TestCase):

    def setUp(self):
        Notifications.store = MockRedis
        self.notifications = [
            {'uuid': 'test', 'type': 'warning', 'title': 'Test Title', 'text': '<p>Test Text</p>'},
            {'uuid': 'second', 'type': 'success', 'title': 'Second title', 'text': 'Test Notification'}
        ]
        Notifications.store.set(Notifications.STORE_KEY, json.dumps(self.notifications))

    def test_list_method_should_return_proper_notifications_list(self):
        self.assertEqual(Notifications.list(), self.notifications)

    @patch('utils.uuid.uuid4', return_value='in-test')
    def test_add_method_should_append_notification_to_list_and_return_uuid(self, uuid4):
        result = Notifications.add('warning', 'No title', 'No text')
        self.assertEqual(result, 'in-test')
        expected_list = self.notifications[:]
        expected_list.append({'uuid': 'in-test', 'type': 'warning', 'title': 'No title', 'text': 'No text'})
        self.assertEqual(Notifications.list(), expected_list)

    def test_remove_method_should_remove_notification_from_list(self):
        Notifications.remove('second')
        expected_list = self.notifications[:1]
        self.assertEqual(Notifications.list(), expected_list)

    def test_remove_method_when_no_such_notification_in_list_should_do_nothing(self):
        Notifications.remove('0de8916f-7595-41b0-8e46-c9eea962b0b8')
        self.assertEqual(Notifications.list(), self.notifications)
