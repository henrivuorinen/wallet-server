import flask
from flask import request, jsonify
import sqlite3
from datetime import datetime

app = flask.Flask(__name__)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_to_db():
    db_file = app.config.get("DB_FILE", "example.sqlite")
    con = sqlite3.connect(db_file, isolation_level='IMMEDIATE')
    con.row_factory = dict_factory
    return con

def create_tables():
    con = connect_to_db()
    cur = con.cursor()

    cur.execute('''
    create table if not exists UserData
(
    Userid         INTEGER
        primary key,
    Name           TEXT,
    Accountbalance DOUBLE
);''')
    cur.execute('''   create table if not exists EventLog
(
    User      INTEGER
        references UserData (UserId),
    EventId   INTEGER
        primary key,
    Timestamp DATETIME,
    Type      TEXT,
    Amount    DOUBLE
);''')
    con.commit()
    con.close()

def create_dummy_data():
    con = connect_to_db()
    cur = con.cursor()
    cur.execute('INSERT INTO UserData(Userid, Name, AccountBalance) VALUES(12345, "Johnny Boy", 100);')
    con.commit()
    con.close()

def format_error(error, code):
    return jsonify({"success": False, "error": error}), code

@app.route('/api/v1/healthcheck', methods=['GET'])
def api_healthcheck():
    return jsonify({"success": True, "message": "System is up and running"})


@app.route('/api/v1/charge', methods=['POST'])
def api_charge():

    json_data = request.get_json()

    #Check values from the request that they are not null
    if 'UserId' in json_data:
        userId = int(json_data['UserId'])
    else:
        return format_error("UserId is missing from the request", 400)
    if 'EventId' in json_data:
        eventId = int(json_data['EventId'])
    else:
        return format_error("EventId is missing from the request", 400)
    if 'Amount' in json_data:
        amount = float(json_data['Amount'])
    else:
        return format_error("Amount is missing from the request", 400)

    con = connect_to_db()
    cur = con.cursor()
    query_result = cur.execute('SELECT Accountbalance FROM UserData WHERE Userid = ?;', [userId]).fetchone()
    if not query_result:
        return format_error("user not found", 404)
    Accountbalance = query_result['Accountbalance']

    existing_event = cur.execute('SELECT Amount, User FROM EventLog WHERE EventId = ?;', [eventId]).fetchone()

    if existing_event:
        if amount == existing_event['Amount'] and userId == existing_event['User']:
            return {"success": True, "UserId": userId, "AccountBalance": Accountbalance}
        else:
            return format_error("Request has a conflict with existing data.", 409)
    if json_data['Amount'] > Accountbalance:
        return format_error("Account balance is too low", 400)
    if json_data['Amount'] < 0:
        return format_error("Amount value is negative", 400)

    cur.execute('INSERT INTO EventLog(User, EventId, Timestamp, Type, Amount) VALUES(?,?,?,?,?);', [userId, eventId, datetime.now(), 'charge', amount])

    updated_balance = Accountbalance - amount
    # Update accountbalance after purchase
    cur.execute('UPDATE UserData SET Accountbalance = ? WHERE Userid = ?;', [updated_balance, userId])
    con.commit()

    cur.close()

    return jsonify({"success": True, "UserId": userId, "AccountBalance": updated_balance})

@app.route('/api/v1/win', methods=['POST'])
def api_win():
    json_data = request.get_json()

    if 'UserId' in json_data:
        userId = int(json_data['UserId'])
    else:
        return format_error("UserId is missing from the request", 400)
    if 'WinningEventId' in json_data:
        win = str(json_data['WinningEventId'])
    else:
        return format_error("WinningEventId is missing from the request", 400)
    if 'Amount' in json_data:
        amount = int(json_data['Amount'])
    else:
        return format_error("Amount is missing from the request", 400)

    #Checking that UserId exists in the DB
    con = connect_to_db()
    cur = con.cursor()
    user_data = cur.execute('SELECT UserId, AccountBalance FROM UserData WHERE UserId = ?;', [userId]).fetchone()
    if not user_data:
        format_error("Userdata not found", 404)

    Accountbalance = user_data['Accountbalance']

    existing_event = cur.execute('SELECT Amount, User FROM EventLog WHERE EventId = ?;', [win]).fetchone()

    if existing_event:
        if amount == existing_event['Amount'] and userId == existing_event['User']:
            return {"success": True, "UserId": userId, "AccountBalance": Accountbalance}
        else:
            return format_error("Request has a conflict with existing data.", 409)
    if not user_data:
        return format_error("Unknown user", 400)
    if amount < 0:
        return format_error("Winning amount is negative", 400)

    updated_balance = amount + Accountbalance

    type = "win"

    cur.execute('INSERT INTO EventLog(User, EventId, Timestamp, Type, Amount) VALUES(?,?,?,?,?);', [userId, win, datetime.now(), type, amount])

    cur.execute('UPDATE UserData SET Accountbalance = ? WHERE Userid = ?;', [updated_balance, userId])

    con.commit()

    cur.close()

    results = {"success": True, "WinningEventId": win, "AccountBalance": updated_balance}

    return jsonify(results)


if __name__ == "__main__":
    create_tables()
    app.run()




