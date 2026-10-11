from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'ff_like_secret_key'

def get_db():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT,
            balance REAL DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            player_id TEXT,
            item_name TEXT,
            price REAL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            trx_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Calculate stats
    total_orders = cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (session['user_id'],)).fetchone()[0]
    total_spent = cursor.execute("SELECT SUM(price) FROM orders WHERE user_id = ? AND status = 'Completed'", (session['user_id'],)).fetchone()[0] or 0
    recent_orders = cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 5", (session['user_id'],)).fetchall()
    
    conn.close()
    return render_template('index.html', user=user, total_orders=total_orders, total_spent=total_spent, recent_orders=recent_orders)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/wallet')
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    deposits = conn.execute("SELECT * FROM deposits WHERE user_id = ? ORDER BY id DESC", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('wallet.html', user=user, deposits=deposits)

@app.route('/buy', methods=['POST'])
def buy():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item_name = request.form['item_name']
    price = float(request.form['price'])
    player_id = request.form['player_id']
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    if user['balance'] < price:
        flash("Insufficient balance! Please add funds.")
        conn.close()
        return redirect(url_for('wallet'))
    
    # Deduct balance
    conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (price, session['user_id']))
    conn.execute("INSERT INTO orders (user_id, player_id, item_name, price) VALUES (?, ?, ?, ?)",
                 (session['user_id'], player_id, item_name, price))
    conn.commit()
    conn.close()
    flash("Order placed successfully!")
    return redirect(url_for('orders'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    amount = float(request.form['amount'])
    trx_id = request.form['trx_id']
    
    conn = get_db()
    conn.execute("INSERT INTO deposits (user_id, amount, trx_id) VALUES (?, ?, ?)",
                 (session['user_id'], amount, trx_id))
    conn.commit()
    conn.close()
    flash("Deposit request submitted!")
    return redirect(url_for('wallet'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('home'))
        else:
            flash("Invalid Credentials")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
            conn.commit()
            conn.close()
            flash("Registration Successful! Please login.")
            return redirect(url_for('login'))
        except:
            conn.close()
            flash("Username already exists!")
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    deposits = conn.execute("SELECT deposits.*, users.username FROM deposits JOIN users ON deposits.user_id = users.id WHERE deposits.status = 'Pending'").fetchall()
    orders = conn.execute("SELECT orders.*, users.username FROM orders JOIN users ON orders.user_id = users.id WHERE orders.status = 'Pending'").fetchall()
    conn.close()
    
    return render_template('admin.html', deposits=deposits, orders=orders)

@app.route('/admin/approve_deposit/<int:id>')
def approve_deposit(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    deposit = conn.execute("SELECT * FROM deposits WHERE id = ?", (id,)).fetchone()
    if deposit and deposit['status'] == 'Pending':
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (deposit['amount'], deposit['user_id']))
        conn.execute("UPDATE deposits SET status = 'Approved' WHERE id = ?", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/approve_order/<int:id>')
def approve_order(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    conn.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
