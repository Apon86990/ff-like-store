from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'ff_like_secret_key_v2'

def get_db():
    conn = sqlite3.connect('store_v3.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
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

# --- HTML TEMPLATES ---

HTML_LOGIN = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - FF Likes Store</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0b1120; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .box { background: #0f172a; padding: 32px 24px; border-radius: 20px; width: 100%; max-width: 360px; border: 1px solid #1e293b; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }
        .logo { font-size: 36px; color: #38bdf8; margin-bottom: 12px; }
        h2 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
        p { font-size: 13px; color: #64748b; margin-bottom: 24px; }
        .google-btn { background: #1e293b; color: #fff; border: 1px solid #334155; width: 100%; padding: 12px; border-radius: 10px; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 10px; cursor: pointer; margin-bottom: 20px; }
        .divider { display: flex; align-items: center; color: #475569; font-size: 12px; margin: 16px 0; }
        .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: #1e293b; }
        .divider span { padding: 0 10px; }
        input { width: 100%; padding: 12px; margin-bottom: 12px; background: #0b1120; color: #fff; border: 1px solid #1e293b; border-radius: 10px; outline: none; font-size: 14px; }
        input:focus { border-color: #38bdf8; }
        button.submit-btn { width: 100%; padding: 12px; background: #0284c7; color: #fff; border: none; border-radius: 10px; font-weight: bold; font-size: 15px; cursor: pointer; }
        .switch { margin-top: 20px; font-size: 13px; color: #64748b; }
        .switch a { color: #38bdf8; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="box">
        <div class="logo"><i class="fa-solid fa-thumbs-up"></i></div>
        <h2>FF LIKES STORE</h2>
        <p>Login to boost your Free Fire profile</p>

        <button class="google-btn" onclick="alert('Google Login configuration required in settings.')">
            <i class="fa-brands fa-google" style="color: #ea4335;"></i> Continue with Google
        </button>

        <div class="divider"><span>OR</span></div>

        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="submit-btn">Sign In</button>
        </form>

        <div class="switch">
            Don't have an account? <a href="/register">Register</a>
        </div>
    </div>
</body>
</html>
'''

HTML_REGISTER = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - FF Likes Store</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0b1120; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .box { background: #0f172a; padding: 32px 24px; border-radius: 20px; width: 100%; max-width: 360px; border: 1px solid #1e293b; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }
        .logo { font-size: 36px; color: #10b981; margin-bottom: 12px; }
        h2 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
        p { font-size: 13px; color: #64748b; margin-bottom: 24px; }
        input { width: 100%; padding: 12px; margin-bottom: 12px; background: #0b1120; color: #fff; border: 1px solid #1e293b; border-radius: 10px; outline: none; font-size: 14px; }
        input:focus { border-color: #10b981; }
        button.submit-btn { width: 100%; padding: 12px; background: #10b981; color: #fff; border: none; border-radius: 10px; font-weight: bold; font-size: 15px; cursor: pointer; }
        .switch { margin-top: 20px; font-size: 13px; color: #64748b; }
        .switch a { color: #10b981; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="box">
        <div class="logo"><i class="fa-solid fa-user-plus"></i></div>
        <h2>Create Account</h2>
        <p>Join FF Likes Store Today</p>

        <form action="/register" method="post">
            <input type="text" name="username" placeholder="Choose Username" required>
            <input type="password" name="password" placeholder="Choose Password" required>
            <button type="submit" class="submit-btn">Register</button>
        </form>

        <div class="switch">
            Already have an account? <a href="/login">Login</a>
        </div>
    </div>
</body>
</html>
'''

HTML_INDEX = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FF LIKES STORE - Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #0b1120; color: #f8fafc; padding-bottom: 90px; }
        .top-nav { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #0f172a; border-bottom: 1px solid #1e293b; }
        .brand { display: flex; align-items: center; gap: 10px; }
        .brand-icon { width: 36px; height: 36px; background: #38bdf8; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #0f172a; }
        .brand-title h3 { font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; }
        .brand-title p { font-size: 11px; color: #64748b; }
        .top-actions { display: flex; align-items: center; gap: 10px; }
        .badge-balance { background: #1e293b; border: 1px solid #334155; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; color: #38bdf8; }
        .avatar { width: 32px; height: 32px; background: #2563eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; }
        .container { padding: 16px; }
        .banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 16px; padding: 16px; margin-bottom: 16px; text-align: center; }
        .banner h2 { font-size: 18px; color: #38bdf8; margin-bottom: 4px; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
        .stat-card { background: #1e293b; border: 1px solid #334155; padding: 14px; border-radius: 14px; display: flex; align-items: center; gap: 12px; }
        .stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .icon-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
        .icon-emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .stat-info h4 { font-size: 18px; font-weight: 700; }
        .stat-info p { font-size: 11px; color: #94a3b8; text-transform: uppercase; }
        .section-title { font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #f1f5f9; }
        .like-cards { display: grid; gap: 12px; margin-bottom: 24px; }
        .package-card { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        .pkg-details h4 { font-size: 16px; color: #38bdf8; margin-bottom: 4px; }
        .pkg-details p { font-size: 14px; font-weight: bold; color: #e2e8f0; }
        .buy-form { display: flex; gap: 8px; }
        .buy-form input { background: #0f172a; border: 1px solid #334155; color: #fff; padding: 8px 12px; border-radius: 8px; font-size: 12px; width: 110px; outline: none; }
        .buy-form button { background: #0284c7; color: #fff; border: none; padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 12px; }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #0f172a; border-top: 1px solid #1e293b; display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 3px; }
        .nav-item.active { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="top-nav">
        <div class="brand">
            <div class="brand-icon"><i class="fa-solid fa-thumbs-up"></i></div>
            <div class="brand-title">
                <h3>FF LIKES STORE</h3>
                <p>PLAYER DASHBOARD</p>
            </div>
        </div>
        <div class="top-actions">
            <div class="badge-balance">৳{{ user.balance }}</div>
            <div class="avatar">{{ user.username[:2].upper() }}</div>
        </div>
    </div>

    <div class="container">
        <div class="banner">
            <h2>Hi, {{ user.username }} 👋</h2>
            <p style="font-size: 12px; color: #94a3b8;">Welcome back to your Like Booster dashboard</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon icon-amber"><i class="fa-solid fa-box"></i></div>
                <div class="stat-info">
                    <h4>{{ total_orders }}</h4>
                    <p>TOTAL ORDERS</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon icon-emerald"><i class="fa-solid fa-coins"></i></div>
                <div class="stat-info">
                    <h4>৳{{ total_spent }}</h4>
                    <p>TOTAL SPENT</p>
                </div>
            </div>
        </div>

        <div class="section-title">🔥 Order Free Fire Likes</div>
        <div class="like-cards">
            <div class="package-card">
                <div class="pkg-details">
                    <h4>100 Likes Instant</h4>
                    <p>৳ 12.00</p>
                </div>
                <form action="/buy" method="post" class="buy-form">
                    <input type="hidden" name="item_name" value="100 Likes Instant">
                    <input type="hidden" name="price" value="12">
                    <input type="text" name="player_id" placeholder="Player UID" required>
                    <button type="submit">Order</button>
                </form>
            </div>

            <div class="package-card">
                <div class="pkg-details">
                    <h4>500 Likes Package</h4>
                    <p>৳ 55.00</p>
                </div>
                <form action="/buy" method="post" class="buy-form">
                    <input type="hidden" name="item_name" value="500 Likes Package">
                    <input type="hidden" name="price" value="55">
                    <input type="text" name="player_id" placeholder="Player UID" required>
                    <button type="submit">Order</button>
                </form>
            </div>

            <div class="package-card">
                <div class="pkg-details">
                    <h4>1000 Likes Mega Pack</h4>
                    <p>৳ 100.00</p>
                </div>
                <form action="/buy" method="post" class="buy-form">
                    <input type="hidden" name="item_name" value="1000 Likes Mega Pack">
                    <input type="hidden" name="price" value="100">
                    <input type="text" name="player_id" placeholder="Player UID" required>
                    <button type="submit">Order</button>
                </form>
            </div>
        </div>
    </div>

    <div class="bottom-nav">
        <a href="/" class="nav-item active"><i class="fa-solid fa-house"></i>Home</a>
        <a href="/orders" class="nav-item"><i class="fa-solid fa-box-archive"></i>Orders</a>
        <a href="/wallet" class="nav-item"><i class="fa-solid fa-wallet"></i>Wallet</a>
        <a href="/logout" class="nav-item"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
    </div>
</body>
</html>
'''

HTML_ORDERS = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Orders - FF Likes Store</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0b1120; color: #fff; padding: 16px; padding-bottom: 90px; }
        h2 { margin-bottom: 16px; font-size: 20px; }
        .order-card { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .order-info h4 { font-size: 15px; color: #38bdf8; margin-bottom: 4px; }
        .order-info p { font-size: 12px; color: #94a3b8; }
        .order-status { font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 20px; }
        .status-pending { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .status-completed { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #0f172a; border-top: 1px solid #1e293b; display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 3px; }
        .nav-item.active { color: #38bdf8; }
    </style>
</head>
<body>
    <h2>My Orders History</h2>
    {% for order in orders %}
    <div class="order-card">
        <div class="order-info">
            <h4>{{ order.item_name }}</h4>
            <p>UID: {{ order.player_id }} | ৳{{ order.price }}</p>
        </div>
        <div class="order-status {% if order.status == 'Completed' %}status-completed{% else %}status-pending{% endif %}">
            {{ order.status }}
        </div>
    </div>
    {% else %}
    <p style="color: #64748b; font-size: 14px;">No orders found yet.</p>
    {% endfor %}

    <div class="bottom-nav">
        <a href="/" class="nav-item"><i class="fa-solid fa-house"></i>Home</a>
        <a href="/orders" class="nav-item active"><i class="fa-solid fa-box-archive"></i>Orders</a>
        <a href="/wallet" class="nav-item"><i class="fa-solid fa-wallet"></i>Wallet</a>
        <a href="/logout" class="nav-item"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
    </div>
</body>
</html>
'''

HTML_WALLET = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Wallet - FF Likes Store</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0b1120; color: #fff; padding: 16px; padding-bottom: 90px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
        .balance-title { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
        .balance-amount { font-size: 28px; font-weight: 800; color: #38bdf8; margin-top: 4px; }
        input, button { width: 100%; padding: 12px; border-radius: 10px; font-size: 14px; margin-bottom: 12px; }
        input { background: #0b1120; border: 1px solid #334155; color: #fff; outline: none; }
        button { background: #0284c7; color: white; border: none; font-weight: bold; cursor: pointer; }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #0f172a; border-top: 1px solid #1e293b; display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 3px; }
        .nav-item.active { color: #38bdf8; }
    </style>
</head>
<body>
    <h2 style="margin-bottom: 16px;">My Wallet</h2>
    <div class="card">
        <div class="balance-title">Current Balance</div>
        <div class="balance-amount">৳{{ user.balance }}</div>
    </div>

    <div class="card">
        <h3 style="font-size: 16px; margin-bottom: 12px;">Add Funds (bKash/Nagad)</h3>
        <p style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">Send Money to: <b>01700000000</b></p>
        <form action="/deposit" method="post">
            <input type="number" name="amount" placeholder="Amount (৳)" required>
            <input type="text" name="trx_id" placeholder="TrxID / Transaction ID" required>
            <button type="submit">Submit Deposit</button>
        </form>
    </div>

    <div class="bottom-nav">
        <a href="/" class="nav-item"><i class="fa-solid fa-house"></i>Home</a>
        <a href="/orders" class="nav-item"><i class="fa-solid fa-box-archive"></i>Orders</a>
        <a href="/wallet" class="nav-item active"><i class="fa-solid fa-wallet"></i>Wallet</a>
        <a href="/logout" class="nav-item"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
    </div>
</body>
</html>
'''

HTML_ADMIN = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - FF Store</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Arial, sans-serif; padding: 20px; }
        h1, h2 { color: #38bdf8; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #1e293b; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
        th { background: #334155; }
        a.btn { background: #10b981; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 14px; }
        a.logout { color: #f87171; float: right; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <a href="/logout" class="logout">Logout</a>
    <h1>👑 Admin Dashboard</h1>
    <br>
    <h2>💵 Pending Deposits</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>User</th>
            <th>Amount</th>
            <th>Trx ID</th>
            <th>Action</th>
        </tr>
        {% for deposit in deposits %}
        <tr>
            <td>{{ deposit.id }}</td>
            <td>{{ deposit.username }}</td>
            <td>৳{{ deposit.amount }}</td>
            <td>{{ deposit.trx_id }}</td>
            <td><a href="/admin/approve_deposit/{{ deposit.id }}" class="btn">Approve</a></td>
        </tr>
        {% else %}
        <tr><td colspan="5">No pending deposits.</td></tr>
        {% endfor %}
    </table>

    <h2>💎 Pending Orders</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>User</th>
            <th>Item</th>
            <th>Player UID</th>
            <th>Price</th>
            <th>Action</th>
        </tr>
        {% for order in orders %}
        <tr>
            <td>{{ order.id }}</td>
            <td>{{ order.username }}</td>
            <td>{{ order.item_name }}</td>
            <td>{{ order.player_id }}</td>
            <td>৳{{ order.price }}</td>
            <td><a href="/admin/approve_order/{{ order.id }}" class="btn">Complete Order</a></td>
        </tr>
        {% else %}
        <tr><td colspan="6">No pending orders.</td></tr>
        {% endfor %}
    </table>
</body>
</html>
'''

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    total_orders = cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (session['user_id'],)).fetchone()[0]
    total_spent = cursor.execute("SELECT SUM(price) FROM orders WHERE user_id = ? AND status = 'Completed'", (session['user_id'],)).fetchone()[0] or 0
    conn.close()
    
    return render_template_string(HTML_INDEX, user=user, total_orders=total_orders, total_spent=total_spent)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],)).fetchall()
    conn.close()
    return render_template_string(HTML_ORDERS, orders=orders)

@app.route('/wallet')
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return render_template_string(HTML_WALLET, user=user)

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
        conn.close()
        return redirect(url_for('wallet'))
    
    conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (price, session['user_id']))
    conn.execute("INSERT INTO orders (user_id, player_id, item_name, price) VALUES (?, ?, ?, ?)",
                 (session['user_id'], player_id, item_name, price))
    conn.commit()
    conn.close()
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
            
    return render_template_string(HTML_LOGIN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            
    return render_template_string(HTML_REGISTER)

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
    
    return render_template_string(HTML_ADMIN, deposits=deposits, orders=orders)

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
    app.run(host='0.0.0.0', port=5000)
