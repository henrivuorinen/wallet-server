import unittest
import requests
import json


class TestObjects(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        "set up test fixtures"
        print("### Setting up flask server ###")
        app = create.app()
        app.config['TESTING'] = True
        self.app = app.test_client()

    @classmethod
    def test_01_health(self):
        """ Test that system is up and running """
        r = self.app.get('http://127.0.0.1:5000/api/v1/healthcheck')
        self.assertEqual(r.status_code, 200)

    def test_02_charge_success(self):
        """ Testing charge endpoint with a request"""
        test_json = {"UserId": 12345, "EventId": 123, "Amount": 1}
        r = self.app.post('http://127.0.0.1:5000/api/v1/charge', data=test_json)
        self.assertEqual(r.status_code, 200)

    def test_03_charge_fail_01(self):
        """ Testing charge endpoint with a bad request"""
        test_json = {"EventId": 21}
        r = self.app.post('http://127.0.0.1:5000/api/v1/charge', data=test_json)
        self.assertEqual(r.status_code, 400)

    def test_04_charge_fail_02(self):
        """ Testing charge endpoint with a conflicting request"""
        test_json = {"UserId": 12345, "EventId": 1, "Amount": 6}
        # Note that db will exists this event already as an example and it has a value of 5
        r = self.app.post('http://127.0.0.1:5000/api/v1/charge', data=test_json)
        self.assertEqual(r.status_code, 409)

    def test_05_win_success(self):
        """ Testing win endpoint with a request"""
        test_json = {"UserId": 12345, "WinningEventId": 123, "Amount": 1}
        r = self.app.post('http://127.0.0.1:5000/api/v1/win', data=test_json)
        self.assertEqual(r.status_code, 200)

    def test_06_win_fail_01(self):
        """ Testing win endpoint with a bad request"""
        test_json = {"WinningEventId": 21}
        r = self.app.post('http://127.0.0.1:5000/api/v1/win', data=test_json)
        self.assertEqual(r.status_code, 400)

    def test_07_charge_fail_02(self):
        """ Testing charge endpoint with a conflicting request"""
        test_json = {"UserId": 12345, "WinningEventId": 1, "Amount": 2}
        # Note that db will exists this event already as an example and it has a value of 5
        r = self.app.post('http://127.0.0.1:5000/api/v1/win', data=test_json)
        self.assertEqual(r.status_code, 409)

