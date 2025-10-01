from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pyrebase
import string
import random
from datetime import datetime
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = "linkforge_secret_key"  # Change this to a secure secret key

# --- Firebase Configuration ---
# IMPORTANT: Keep your Firebase credentials secure and do not expose them publicly.
firebaseConfig = {
    "apiKey": "AIzaSyBgwvQkoISPUSH2MiHVvHNtJilrwALjotI",
    "authDomain": "codekrafter-16f24.firebaseapp.com",
    "databaseURL": "https://codekrafter-16f24-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "codekrafter-16f24",
    "storageBucket": "codekrafter-16f24.firebasestorage.app",
    "messagingSenderId": "63322060037",
    "appId": "1:63322060037:web:61d0217cae791aee12736c",
};

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# --- Helper Functions ---
def generate_short_code(length=7):
    """Generates a random alphanumeric short code."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def sanitize_email(email):
    """Replaces invalid Firebase key characters in an email address."""
    return email.replace('.', '_').replace('@', '_')

# --- Main Routes ---
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        user_email = session['user']
        safe_email = sanitize_email(user_email)
        user_links = []
        try:
            # Fetch all links for the current user
            links_node = db.child("links").child(safe_email).get()
            if links_node.val():
                for link in links_node.each():
                    link_data = link.val()
                    link_data['short_code'] = link.key() # Add short_code for QR generation
                    user_links.append(link_data)
        except Exception as e:
            print(f"Error fetching links: {e}")
        
        # Sort links by date, newest first
        user_links.sort(key=lambda x: x.get('date', '1970-01-01T00:00:00'), reverse=True)

        return render_template('dashboard.html', user_links=user_links)
    return redirect(url_for('index'))

# --- URL Management ---
@app.route('/shorten', methods=['POST'])
def shorten():
    if 'user' in session:
        long_url = request.form['url']
        short_code = generate_short_code()
        safe_email = sanitize_email(session['user'])

        data = {
            "original": long_url,
            "short": f"{request.host_url}{short_code}",
            "clicks": 0,
            "date": datetime.utcnow().isoformat() # Store date in standard ISO format
        }
        
        db.child("links").child(safe_email).child(short_code).set(data)
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))

@app.route('/<short_code>')
def redirect_to_url(short_code):
    try:
        all_users_links = db.child("links").get()
        if all_users_links.val():
            for user in all_users_links.each():
                user_key = user.key()
                link_node = db.child("links").child(user_key).child(short_code)
                link_data = link_node.get().val()
                
                if link_data:
                    # Increment the click count
                    link_node.update({"clicks": link_data.get('clicks', 0) + 1})
                    return redirect(link_data['original'])
    except Exception as e:
        print(f"Error during redirect: {e}")
    
    return render_template('404.html'), 404

# --- QR Code Generation ---
@app.route('/qr/<short_code>')
def generate_qr(short_code):
    """Dynamically generates a QR code image for a short URL."""
    short_url = f"{request.host_url}{short_code}"
    img_buffer = BytesIO()
    qr_img = qrcode.make(short_url)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email
            return redirect(url_for('dashboard'))
        except:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            auth.create_user_with_email_and_password(email, password)
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('signup.html', error="Email already exists or is invalid.")
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- Static Pages ---
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run(debug=True)
