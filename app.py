from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import os
import requests
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'ff_like_google_login_secret_key_v7'

# --- GOOGLE OAUTH CONFIGURATION ---
GOOGLE_CLIENT_ID = '779765298647-unvnl1t09js256rufltacdb4gn8o1g2b.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

NAGAD_NUMBER = "01606837021"

def get_db():
    conn = sqlite3.connect('store_v7.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
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
            trx_id TEXT UNIQUE,
            status TEXT DEFAULT 'Completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, full_name, password, role) VALUES ('admin', 'Admin', 'admin123', 'admin')")
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
    <title>Login - GHOST X LIKES</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background: #050b14; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .box { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); padding: 36px 28px; border-radius: 24px; width: 100%; max-width: 380px; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7); text-align: center; }
        .logo { font-size: 42px; background: linear-gradient(135deg, #0284c7, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }
        h2 { font-size: 22px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 6px; }
        p { font-size: 13px; color: #64748b; margin-bottom: 28px; }
        .google-btn { background: rgba(255, 255, 255, 0.05); color: #fff; border: 1px solid rgba(255, 255, 255, 0.15); width: 100%; padding: 14px; border-radius: 14px; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 12px; cursor: pointer; text-decoration: none; transition: 0.3s; }
        .google-btn:hover { background: rgba(255, 255, 255, 0.1); }
        .divider { display: flex; align-items: center; color: #475569; font-size: 12px; margin: 20px 0; }
        .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1); }
        .divider span { padding: 0 10px; }
        input { width: 100%; padding: 13px; margin-bottom: 14px; background: #080f1e; color: #fff; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; outline: none; font-size: 14px; }
        input:focus { border-color: #38bdf8; }
        button.submit-btn { width: 100%; padding: 13px; background: linear-gradient(135deg, #0284c7, #0369a1); color: #fff; border: none; border-radius: 12px; font-weight: bold; font-size: 15px; cursor: pointer; }
        .switch { margin-top: 22px; font-size: 13px; color: #64748b; }
        .switch a { color: #38bdf8; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="box">
        <div class="logo"><i class="fa-solid fa-thumbs-up"></i></div>
        <h2>GHOST X LIKES</h2>
        <p>Login to boost your Free Fire profile</p>

        <a href="/login/google" class="google-btn">
            <i class="fa-brands fa-google" style="color: #ea4335; font-size: 18px;"></i> Continue with Google
        </a>

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

HTML_INDEX = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GHOST X LIKES - Player Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #030712; color: #f8fafc; padding-bottom: 100px; min-height: 100vh; }
        
        .top-nav { display: flex; justify-content: space-between; align-items: center; padding: 18px 16px; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255, 255, 255, 0.08); sticky: top: 0; z-index: 90; }
        .brand { display: flex; align-items: center; gap: 12px; }
        .brand-icon { width: 40px; height: 40px; background: linear-gradient(135deg, #0284c7, #38bdf8); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3); }
        .brand-title h3 { font-size: 16px; font-weight: 800; letter-spacing: 0.5px; }
        .brand-title p { font-size: 10px; color: #64748b; font-weight: 700; letter-spacing: 0.5px; }
        
        .top-actions { display: flex; align-items: center; gap: 10px; }
        .badge-balance { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 6px; }
        .icon-btn { width: 34px; height: 34px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 14px; }
        .avatar { width: 36px; height: 36px; background: linear-gradient(135deg, #2563eb, #1d4ed8); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; border: 2px solid rgba(255,255,255,0.1); }
        
        .container { padding: 18px 16px; }
        
        .header-card { background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6)); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 20px; margin-bottom: 20px; backdrop-filter: blur(10px); }
        .greeting { font-size: 15px; color: #94a3b8; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
        .balance-label { font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.5px; margin-top: 10px; }
        .balance-amount { font-size: 32px; font-weight: 900; color: #fff; margin-bottom: 18px; }
        
        .action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .btn-primary-action { background: linear-gradient(135deg, #0284c7, #0369a1); color: #fff; padding: 12px; border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.25); }
        .btn-secondary-action { background: rgba(255, 255, 255, 0.05); color: #fff; border: 1px solid rgba(255, 255, 255, 0.12); padding: 12px; border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 8px; }
        
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 22px; }
        .stat-card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.06); padding: 14px; border-radius: 16px; display: flex; align-items: center; gap: 12px; }
        .stat-icon { width: 38px; height: 38px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .purple-icon { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
        .teal-icon { background: rgba(20, 184, 166, 0.15); color: #2dd4bf; }
        .amber-icon { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
        .rose-icon { background: rgba(244, 63, 94, 0.15); color: #fb7185; }
        .stat-info h5 { font-size: 17px; font-weight: 800; }
        .stat-info p { font-size: 10px; color: #64748b; font-weight: 700; text-transform: uppercase; }
        
        .section-header { font-size: 12px; font-weight: 800; text-transform: uppercase; color: #64748b; letter-spacing: 0.8px; margin-bottom: 14px; }
        
        .package-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .pkg-info h4 { font-size: 15px; color: #38bdf8; font-weight: 700; margin-bottom: 2px; }
        .pkg-info p { font-size: 14px; font-weight: 800; color: #fff; }
        .buy-form { display: flex; gap: 8px; }
        .buy-form input { background: #080f1e; border: 1px solid rgba(255,255,255,0.1); color: #fff; padding: 10px 12px; border-radius: 10px; font-size: 12px; width: 110px; outline: none; }
        .buy-form button { background: linear-gradient(135deg, #0284c7, #0369a1); color: #fff; border: none; padding: 10px 16px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 12px; }

        .bottom-nav { position: fixed; bottom: 16px; left: 16px; right: 16px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; display: flex; justify-content: space-around; align-items: center; padding: 12px 8px; z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; font-weight: 600; flex: 1; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 4px; }
        .nav-item.active { color: #38bdf8; }
        
        .nav-center-btn { width: 48px; height: 48px; background: linear-gradient(135deg, #0284c7, #38bdf8); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.5); transform: translateY(-16px); text-decoration: none; border: 4px solid #030712; }
    </style>
</head>
<body>
    <div class="top-nav">
        <div class="brand">
            <div class="brand-icon"><i class="fa-solid fa-bolt"></i></div>
            <div class="brand-title">
                <h3>GHOST X LIKES</h3>
                <p>PLAYER DASHBOARD</p>
            </div>
        </div>
        <div class="top-actions">
            <div class="badge-balance"><i class="fa-solid fa-wallet" style="font-size:12px;"></i> ৳{{ "%.2f"|format(user.balance) }}</div>
            <div class="icon-btn"><i class="fa-regular fa-bell"></i></div>
            <div class="avatar">{{ user.full_name[:2].upper() if user.full_name else user.username[:2].upper() }}</div>
        </div>
    </div>

    <div class="container">
        <div class="header-card">
            <div class="greeting">👋 Hi, <b>{{ user.full_name or user.username }}</b></div>
            <div class="balance-label">AVAILABLE BALANCE</div>
            <div class="balance-amount">৳{{ "%.2f"|format(user.balance) }}</div>
            
            <div class="action-row">
                <a href="#packages" class="btn-primary-action"><i class="fa-solid fa-bolt"></i> Order likes</a>
                <a href="/wallet" class="btn-secondary-action"><i class="fa-solid fa-plus"></i> Add funds</a>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon purple-icon"><i class="fa-solid fa-heart"></i></div>
                <div class="stat-info">
                    <h5>0</h5>
                    <p>LIKES RECEIVED</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon teal-icon"><i class="fa-solid fa-bolt"></i></div>
                <div class="stat-info">
                    <h5>0</h5>
                    <p>ACTIVE BOOSTS</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon amber-icon"><i class="fa-solid fa-box"></i></div>
                <div class="stat-info">
                    <h5>{{ total_orders }}</h5>
                    <p>ORDERS</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon rose-icon"><i class="fa-solid fa-coins"></i></div>
                <div class="stat-info">
                    <h5>৳{{ "%.0f"|format(total_spent) }}</h5>
                    <p>TOTAL SPENT</p>
                </div>
            </div>
        </div>

        <div class="section-header" id="packages">🔥 SELECT FREE FIRE LIKES PACKAGE</div>
        
        <div class="package-card">
            <div class="pkg-info">
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
            <div class="pkg-info">
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
            <div class="pkg-info">
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

    <div class="bottom-nav">
        <a href="/" class="nav-item active"><i class="fa-solid fa-house"></i>Home</a>
        <a href="/orders" class="nav-item"><i class="fa-solid fa-box"></i>Orders</a>
        <a href="#packages" class="nav-center-btn"><i class="fa-solid fa-bolt"></i></a>
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
    <title>Wallet - Auto Nagad Deposit</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #030712; color: #fff; padding: 18px; padding-bottom: 100px; }
        .card { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 22px; margin-bottom: 20px; }
        .balance-title { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .balance-amount { font-size: 32px; font-weight: 900; color: #38bdf8; margin-top: 4px; }
        
        .nagad-box { background: linear-gradient(135deg, #d97706, #b45309); border-radius: 16px; padding: 16px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; }
        .nagad-title { font-size: 16px; font-weight: 800; color: #fff; }
        .nagad-num { font-size: 18px; font-weight: 900; color: #fef08a; font-family: monospace; }
        
        input, button { width: 100%; padding: 14px; border-radius: 12px; font-size: 14px; margin-bottom: 12px; }
        input { background: #080f1e; border: 1px solid rgba(255,255,255,0.1); color: #fff; outline: none; }
        input:focus { border-color: #38bdf8; }
        button { background: linear-gradient(135deg, #0284c7, #0369a1); color: white; border: none; font-weight: 800; cursor: pointer; }
        
        .bottom-nav { position: fixed; bottom: 16px; left: 16px; right: 16px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; display: flex; justify-content: space-around; align-items: center; padding: 12px 8px; z-index: 100; }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; font-weight: 600; flex: 1; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 4px; }
        .nav-item.active { color: #38bdf8; }
        .nav-center-btn { width: 48px; height: 48px; background: linear-gradient(135deg, #0284c7, #38bdf8); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.5); transform: translateY(-16px); text-decoration: none; border: 4px solid #030712; }
    </style>
</head>
<body>
    <h2 style="margin-bottom: 18px; font-size: 20px;">My Wallet</h2>
    <div class="card">
        <div class="balance-title">Current Balance</div>
        <div class="balance-amount">৳{{ "%.2f"|format(user.balance) }}</div>
    </div>

    <div class="card">
        <div class="nagad-box">
            <div>
                <div class="nagad-title"><i class="fa-solid fa-mobile-screen-button"></i> Nagad Personal</div>
                <div style="font-size: 11px; opacity: 0.9;">Send Money Only</div>
            </div>
            <div class="nagad-num">{{ nagad_number }}</div>
        </div>

        <h4 style="font-size: 14px; margin-bottom: 12px; color: #94a3b8;">⚡ Auto Add Money (Instant Verification)</h4>
        
        {% if msg %}
        <p style="color: #34d399; font-size: 13px; margin-bottom: 12px;">{{ msg }}</p>
        {% endif %}

        <form action="/deposit" method="post">
            <input type="number" step="any" name="amount" placeholder="Enter Amount (৳)" required>
            <input type="text" name="trx_id" placeholder="Nagad TrxID (e.g. 71A8B...)" required>
            <button type="submit">Verify & Add Balance Automatically</button>
        </form>
    </div>

    <div class="bottom-nav">
        <a href="/" class="nav-item"><i class="fa-solid fa-house"></i>Home</a>
        <a href="/orders" class="nav-item"><i class="fa-solid fa-box"></i>Orders</a>
        <a href="/" class="nav-center-btn"><i class="fa-solid fa-bolt"></i></a>
        <a href="/wallet" class="nav-item active"><i class="fa-solid fa-wallet"></i>Wallet</a>
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
    <title>My Orders - GHOST X LIKES</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #030712; color: #fff; padding: 18px; padding-bottom: 100px; }
        h2 { margin-bottom: 18px; font-size: 20px; }
        .order-card { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .order-info h4 { font-size: 15px; color: #38bdf8; font-weight: 700; margin-bottom: 4px; }
        .order-info p { font-size: 12px; color: #94a3b8; }
        .order-status { font-size: 11px; font-weight: 800; padding: 5px 12px; border-radius: 20px; text-transform: uppercase; }
        .status-pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .status-completed { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .bottom-nav { position: fixed; bottom: 16px; left: 16px; right: 16px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; display: flex; justify-content: space-around; align-items: center; padding: 12px 8px; z-index: 100; }
        .nav-item { text-align: center; color: #64748b; text-decoration: none; font-size: 11px; font-weight: 600; flex: 1; }
        .nav-item i { font-size: 18px; display: block; margin-bottom: 4px; }
        .nav-item.active { color: #38bdf8; }
        .nav-center-btn { width: 48px; height: 48px; background: linear-gradient(135deg, #0284c7, #38bdf8); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.5); transform: translateY(-16px); text-decoration: none; border: 4px solid #030712; }
    </style>
</head>
<body>
    <h2>Recent Orders</h2>
    {% for order in orders %}
    <div class="order-card">
        <div class="order-info">
            <h4>{{ order.item_name }}</h4>
            <p>UID: <b>{{ order.player_id }}</b> • ৳{{ order.price }}</p>
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
        <a href="/orders" class="nav-item active"><i class="fa-solid fa-box"></i>Orders</a>
        <a href="/" class="nav-center-btn"><i class="fa-solid fa-bolt"></i></a>
        <a href="/wallet" class="nav-item"><i class="fa-solid fa-wallet"></i>Wallet</a>
        <a href="/logout" class="nav-item"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
    </div>
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
    msg = request.args.get('msg')
    conn.close()
    return render_template_string(HTML_WALLET, user=user, nagad_number=NAGAD_NUMBER, msg=msg)

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
        return redirect(url_for('wallet', msg="Insufficient balance! Please add funds via Nagad."))
    
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
    
    try:
        amount = float(request.form['amount'])
        trx_id = request.form['trx_id'].strip()
        
        conn = get_db()
        conn.execute("INSERT INTO deposits (user_id, amount, trx_id, status) VALUES (?, ?, ?, 'Completed')",
                     (session['user_id'], amount, trx_id))
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('wallet', msg=f"Success! ৳{amount} added to your account instantly."))
    except Exception as e:
        return redirect(url_for('wallet', msg="Invalid or duplicate TrxID! Please try again."))

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
            session['full_name'] = user['full_name']
            return redirect(url_for('home'))
            
    return render_template_string(HTML_LOGIN)

# --- GOOGLE OAUTH ROUTES ---
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def google_auth():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
    
    google_email = user_info['email']
    google_name = user_info.get('given_name') or user_info.get('name') or google_email.split('@')[0]
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (google_email,)).fetchone()
    
    if not user:
        conn.execute("INSERT INTO users (username, full_name, password, role) VALUES (?, ?, ?, ?)",
                     (google_email, google_name, 'google_authenticated', 'user'))
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (google_email,)).fetchone()
    else:
        conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (google_name, user['id']))
        conn.commit()
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = google_name
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
