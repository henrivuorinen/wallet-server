import os
import pytest
import tempfile
from app import app, create_tables, create_dummy_data

@pytest.fixture
def client():
    db_fd, app.config['DB_FILE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            create_tables()
            create_dummy_data()
        yield client

    os.close(db_fd)
    os.unlink(app.config['DB_FILE'])


def test_health(client):
    """ Test that system is up and running """
    r = client.get('/api/v1/healthcheck')
    assert r.status_code == 200

def test_charge_success(client):
    """ Testing charge endpoint with a request"""
    test_json = {"UserId": 12345, "EventId": 123, "Amount": 1}
    r = client.post('/api/v1/charge', json=test_json)
    assert r.status_code == 200

def test_charge_fail(client):
    """ Testing charge endpoint with a conflicting request"""
    test_json1 = {"UserId": 12345, "EventId": 123, "Amount": 1}
    r = client.post('/api/v1/charge', json=test_json1)
    assert r.status_code == 200
    test_json2 = {"UserId": 12345, "EventId": 123, "Amount": 6}
    r = client.post('/api/v1/charge', json=test_json2)
    assert r.status_code == 409

def test_duplicate_charge(client):
    """ Testing charge endpoint with a duplicate requests"""
    test_json = {"UserId": 12345, "EventId": 123, "Amount": 1}
    r1 = client.post('/api/v1/charge', json=test_json)
    assert r1.status_code == 200
    r2 = client.post('/api/v1/charge', json=test_json)
    assert r2.status_code == 200
    r1.json['AccountBalance'] == r2.json['AccountBalance']

def test_win_success(client):
    """ Testing win endpoint with a request"""
    test_json = {"UserId": 12345, "WinningEventId": 123, "Amount": 1}
    r = client.post('/api/v1/win', json=test_json)
    assert r.status_code == 200

def test_win_fail_01(client):
    """ Testing win endpoint with a bad request"""
    test_json = {"WinningEventId": 21}
    r = client.post('/api/v1/win', json=test_json)
    assert r.status_code == 400

def test_win_fail_02(client):
    """ Testing charge endpoint with a conflicting request"""
    test_json1 = {"UserId": 12345, "WinningEventId": 123, "Amount": 1}
    r = client.post('/api/v1/win', json=test_json1)
    assert r.status_code == 200
    test_json2 = {"UserId": 12345, "WinningEventId": 123, "Amount": 2}
    r = client.post('/api/v1/win', json=test_json2)
    assert r.status_code == 409


