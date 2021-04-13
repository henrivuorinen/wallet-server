import flask
from flask import request, jsonify
import sqlite3
from datetime import datetime
import json

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_to_db():
    con = sqlite3.connect('example.sqlite', isolation_level='IMMEDIATE')
    con.row_factory = dict_factory
    return con

def format_error(error, code):
    return jsonify({"success": False, "error": error}), code


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
        return format_error("Unknown user", 400)

    Accountbalance = user_data['Accountbalance']

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


app.run()




