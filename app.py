import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ff_store_secret_key_12345')

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Deposits Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            trx_id TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            item_name TEXT NOT NULL,
            player_id TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    # Admin User Creation (if not exists)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()
    
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('home'))
        else:
            return "Invalid Username or Password!"
            
    return render_template('login.html') if os.path.exists('templates/login.html') else '''
        <form method="post">
            <h2>Login</h2>
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!"
            
    return render_template('register.html') if os.path.exists('templates/register.html') else '''
        <form method="post">
            <h2>Register</h2>
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <input type="submit" value="Register">
        </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    amount = request.form.get('amount')
    trx_id = request.form.get('trx_id')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO deposits (username, amount, trx_id) VALUES (?, ?, ?)',
                 (session['username'], amount, trx_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/buy', methods=['POST'])
def buy():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    item_name = request.form.get('item_name')
    player_id = request.form.get('player_id')
    price = float(request.form.get('price', 0))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    
    if user['balance'] >= price:
        # Deduct balance & add order
        new_balance = user['balance'] - price
        conn.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, session['username']))
        conn.execute('INSERT INTO orders (username, item_name, player_id, price) VALUES (?, ?, ?, ?)',
                     (session['username'], item_name, player_id, price))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    else:
        conn.close()
        return "Insufficient Balance!"

@app.route('/admin')
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return "Access Denied!"
        
    conn = get_db_connection()
    deposits = conn.execute('SELECT * FROM deposits WHERE status = "Pending"').fetchall()
    orders = conn.execute('SELECT * FROM orders WHERE status = "Pending"').fetchall()
    conn.close()
    
    return render_template('admin.html', deposits=deposits, orders=orders)

@app.route('/admin/approve_deposit/<int:id>')
def approve_deposit(id):
    if 'role' not in session or session['role'] != 'admin':
        return "Access Denied!"
        
    conn = get_db_connection()
    deposit = conn.execute('SELECT * FROM deposits WHERE id = ?', (id,)).fetchone()
    
    if deposit and deposit['status'] == 'Pending':
        conn.execute('UPDATE deposits SET status = "Approved" WHERE id = ?', (id,))
        conn.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (deposit['amount'], deposit['username']))
        conn.commit()
        
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/approve_order/<int:id>')
def approve_order(id):
    if 'role' not in session or session['role'] != 'admin':
        return "Access Denied!"
        
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = "Completed" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

