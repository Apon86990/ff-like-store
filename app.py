import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Config
NAGAD_NUMBER = "01700000000"  # Apnar Nagad Personal/Merchant Number
ADMIN_KEY = "apon1234"         # Admin Panel Access Key

def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trx_id TEXT UNIQUE,
            amount REAL,
            user_id TEXT,
            status TEXT DEFAULT 'APPROVED'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            player_id TEXT,
            item_name TEXT,
            price REAL,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html', nagad_num=NAGAD_NUMBER)

@app.route('/api/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'})
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return jsonify({'success': True, 'balance': balance})

@app.route('/api/verify_deposit', methods=['POST'])
def verify_deposit():
    data = request.json
    user_id = data.get('user_id')
    trx_id = data.get('trx_id')
    amount = float(data.get('amount', 0))

    if not user_id or not trx_id or amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid data submitted'})

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO deposits (trx_id, amount, user_id) VALUES (?, ?, ?)", (trx_id, amount, user_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'{amount} BDT added to account successfully!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Transaction ID already used!'})

@app.route('/api/buy_item', methods=['POST'])
def buy_item():
    data = request.json
    user_id = data.get('user_id')
    player_id = data.get('player_id')
    item_name = data.get('item_name')
    price = float(data.get('price', 0))

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row or row[0] < price:
        conn.close()
        return jsonify({'success': False, 'message': 'Insufficient Balance! Please deposit first.'})

    # Deduct balance
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
    cursor.execute("INSERT INTO orders (user_id, player_id, item_name, price) VALUES (?, ?, ?, ?)", 
                   (user_id, player_id, item_name, price))
    conn.commit()

    # Automate API Order to fflikebd.site
    try:
        api_res = requests.post("https://fflikebd.site/api/order", json={
            "player_id": player_id,
            "package": item_name
        }, timeout=10)
        status = 'COMPLETED' if api_res.status_code == 200 else 'PROCESSING'
    except Exception:
        status = 'PROCESSING'

    cursor.execute("UPDATE orders SET status = ? WHERE id = (SELECT max(id) FROM orders)", (status,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'Order placed successfully! Status: {status}'})

@app.route('/admin')
def admin_panel():
    key = request.args.get('key')
    if key != ADMIN_KEY:
        return "Unauthorized Access", 403

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.execute("SELECT * FROM deposits ORDER BY id DESC")
    deposits = cursor.fetchall()
    conn.close()

    return render_template('admin.html', orders=orders, deposits=deposits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
