# Hostel Feedback System with SQLite Database
# Streamlit Application - Complete Code

import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime
import hashlib
from streamlit_lottie import st_lottie
import requests
import json
import os
from contextlib import contextmanager

# ======================
# CONFIGURATION
# ======================
st.set_page_config(
    page_title="Hostel Feedback System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# DATABASE CONFIGURATION
# ======================
# SQLite Database Configuration
DB_PATH = "hostel_feedback.db"

# ======================
# SECURITY SETTINGS
# ======================
# ADMIN CREDENTIALS [CHANGE THESE IN PRODUCTION]
ADMIN_USERNAME = "hostel_admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("SecureAdminPass123!".encode()).hexdigest()

# ======================
# DATABASE CONNECTION MANAGEMENT
# ======================
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row  # Enable column access by name
        yield connection
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        yield None
    finally:
        if connection:
            connection.close()

def initialize_database():
    """Create database tables if they don't exist"""
    create_tables_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        reg_no TEXT NOT NULL,
        room_no TEXT NOT NULL,
        last_login DATETIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Feedback table
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        hostel_feedback TEXT,
        hostel_rating TEXT NOT NULL CHECK (hostel_rating IN ('A', 'B', 'C', 'D', 'E')),
        mess_feedback TEXT,
        mess_type TEXT NOT NULL CHECK (mess_type IN ('Veg', 'Non-Veg', 'Special', 'Food-Park')),
        mess_rating TEXT NOT NULL CHECK (mess_rating IN ('A', 'B', 'C', 'D', 'E')),
        bathroom_feedback TEXT,
        bathroom_rating TEXT NOT NULL CHECK (bathroom_rating IN ('A', 'B', 'C', 'D', 'E')),
        other_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
    );

    -- Admin logs table
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.executescript(create_tables_sql)
                connection.commit()
                return True
    except sqlite3.Error as e:
        st.error(f"Database initialization error: {e}")
        return False
    return False

# ======================
# HELPER FUNCTIONS
# ======================
def hash_password(password):
    """Securely hash passwords using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_lottieurl(url):
    """Load Lottie animations from URL"""
    try:
        r = requests.get(url, timeout=5)
        return None if r.status_code != 200 else r.json()
    except:
        return None

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False

def log_admin_action(action, details=""):
    """Record admin activities"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                timestamp = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO admin_logs (timestamp, action, details) VALUES (?, ?, ?)",
                    (timestamp, action, details)
                )
                connection.commit()
    except sqlite3.Error as e:
        st.error(f"Error logging admin action: {e}")

# ======================
# DATABASE OPERATIONS
# ======================
def get_user_count():
    """Get total number of registered users"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                return count
    except sqlite3.Error as e:
        st.error(f"Error getting user count: {e}")
    return 0

def get_feedback_count():
    """Get total number of feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM feedback")
                count = cursor.fetchone()[0]
                return count
    except sqlite3.Error as e:
        st.error(f"Error getting feedback count: {e}")
    return 0

def get_recent_feedback(limit=5):
    """Get recent feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT username, timestamp, hostel_rating, mess_type, mess_rating, 
                       bathroom_rating, other_comments 
                FROM feedback 
                ORDER BY timestamp DESC 
                LIMIT ?
                """
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting recent feedback: {e}")
    return pd.DataFrame()

def get_all_feedback():
    """Get all feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting all feedback: {e}")
    return pd.DataFrame()

def get_all_users():
    """Get all users (without passwords)"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT username, name, email, reg_no, room_no, last_login, created_at 
                FROM users 
                ORDER BY created_at DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting all users: {e}")
    return pd.DataFrame()

def get_admin_logs():
    """Get all admin logs"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM admin_logs ORDER BY timestamp DESC")
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting admin logs: {e}")
    return pd.DataFrame()

# ======================
# AUTHENTICATION FUNCTIONS
# ======================
def authenticate_admin(username, password):
    """Verify admin credentials"""
    return (username == ADMIN_USERNAME and 
            hash_password(password) == ADMIN_PASSWORD_HASH)

def authenticate_user(username, password):
    """Verify student credentials"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT username FROM users WHERE username = ? AND password = ?",
                    (username, hash_password(password))
                )
                result = cursor.fetchone()
                
                if result:
                    # Update last login
                    cursor.execute(
                        "UPDATE users SET last_login = ? WHERE username = ?",
                        (datetime.now().isoformat(), username)
                    )
                    connection.commit()
                    return True
    except sqlite3.Error as e:
        st.error(f"Authentication error: {e}")
    return False

def register_user(username, password, user_data):
    """Register new student"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                
                # Check if username already exists
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, "Username already exists"
                
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (username, password, name, email, reg_no, room_no) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    username, 
                    hash_password(password),
                    user_data['name'],
                    user_data['email'],
                    user_data['reg_no'],
                    user_data['room_no']
                ))
                connection.commit()
                return True, "Registration successful"
                
    except sqlite3.Error as e:
        return False, f"Registration error: {e}"

def delete_user(username):
    """Delete a user from database"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                connection.commit()
                return True
    except sqlite3.Error as e:
        st.error(f"Error deleting user: {e}")
    return False

# ======================
# FEEDBACK FUNCTIONS
# ======================
def submit_feedback(username, feedback_data):
    """Submit new feedback"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO feedback (
                        username, timestamp, hostel_feedback, hostel_rating,
                        mess_feedback, mess_type, mess_rating, bathroom_feedback,
                        bathroom_rating, other_comments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    datetime.now().isoformat(),
                    feedback_data['hostel_feedback'],
                    feedback_data['hostel_rating'],
                    feedback_data['mess_feedback'],
                    feedback_data['mess_type'],
                    feedback_data['mess_rating'],
                    feedback_data['bathroom_feedback'],
                    feedback_data['bathroom_rating'],
                    feedback_data['other_comments']
                ))
                connection.commit()
                return True
    except sqlite3.Error as e:
        st.error(f"Error submitting feedback: {e}")
    return False

def clear_admin_logs():
    """Clear all admin logs"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM admin_logs")
                connection.commit()
                return True
    except sqlite3.Error as e:
        st.error(f"Error clearing logs: {e}")
    return False

# ======================
# UI COMPONENTS
# ======================
def show_admin_sidebar():
    """Admin-specific sidebar options"""
    st.sidebar.header("Admin Controls")
    st.sidebar.success("✅ Admin Logged In")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout Admin", type="primary"):
        # Clear admin session
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.is_admin = False
        log_admin_action("ADMIN_LOGOUT")
        st.success("Admin logged out successfully!")
        time.sleep(1)
        st.rerun()

def show_user_sidebar():
    """Regular user sidebar options"""
    st.sidebar.header(f"Welcome {st.session_state.current_user}")
    
    # Show current login status
    st.sidebar.success("✅ Logged In")
    
    if st.sidebar.button("🚪 Logout"):
        # Clear login session
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.is_admin = False
        st.success("Logged out successfully!")
        time.sleep(1)
        st.rerun()

def render_login_page():
    """Login page with tabs for admin/student"""
    st.title("🔒 Authentication")
    
    login_tab, admin_tab = st.tabs(["Student Login", "Admin Login"])
    
    with login_tab:
        with st.form("student_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary"):
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with admin_tab:
        with st.form("admin_login"):
            st.warning("Administrative Access Only")
            admin_user = st.text_input("Admin Username")
            admin_pass = st.text_input("Admin Password", type="password")
            
            if st.form_submit_button("Admin Login", type="primary"):
                if authenticate_admin(admin_user, admin_pass):
                    st.session_state.is_admin = True
                    st.session_state.logged_in = True
                    st.session_state.current_user = "admin"
                    log_admin_action("ADMIN_LOGIN")
                    st.success("Admin access granted!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")

# ======================
# MAIN APPLICATION
# ======================
def main():
    # Initialize session state
    init_session_state()
    
    # Initialize database on first run
    if not st.session_state.db_initialized:
        if initialize_database():
            st.session_state.db_initialized = True
        else:
            st.error("Failed to initialize database.")
            st.stop()
    
    # Debug info (remove in production)
    if st.sidebar.checkbox("Show Debug Info", value=False):
        st.sidebar.write("Session State:")
        st.sidebar.write(f"Logged in: {st.session_state.get('logged_in', False)}")
        st.sidebar.write(f"Current user: {st.session_state.get('current_user', 'None')}")
        st.sidebar.write(f"Is admin: {st.session_state.get('is_admin', False)}")
        st.sidebar.write(f"DB initialized: {st.session_state.get('db_initialized', False)}")
        st.sidebar.write(f"Database file exists: {os.path.exists(DB_PATH)}")
    
    # Sidebar Navigation
    st.sidebar.title("Hostel Feedback System")
    
    # Show appropriate sidebar based on login state
    if st.session_state.get('is_admin'):
        show_admin_sidebar()
    elif st.session_state.get('logged_in'):
        show_user_sidebar()
    else:
        st.sidebar.info("Please login to access all features")
    
    # Navigation options based on authentication status
    if st.session_state.get('is_admin'):
        pages = {
            "Dashboard": admin_dashboard,
            "View Feedback": feedback_viewer,
            "User Management": user_manager,
            "System Logs": system_logs
        }
    elif st.session_state.get('logged_in'):
        pages = {
            "Home": home_page,
            "Submit Feedback": feedback_page,
            "FAQ": faq_page
        }
    else:
        pages = {
            "Home": home_page,
            "Register": register_page,
            "Login": render_login_page,
            "FAQ": faq_page
        }
    
    # Handle page selection
    page = st.sidebar.selectbox("Menu", list(pages.keys()))
    
    # Execute the selected page function
    try:
        pages[page]()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try refreshing the page or contact support.")

# ======================
# PAGE COMPONENTS
# ======================
def home_page():
    st.title("Welcome to Hostel Feedback System")
    st.subheader("Your voice matters!")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        ### About This System
        - Submit feedback about hostel facilities
        - Rate mess food quality (Veg/Non-Veg/Special/Food-Park)
        - Report bathroom cleanliness issues
        - Help improve hostel living conditions
            
        **Please login to submit feedback**
        """)
        
    with col2:
        if lottie_feedback := load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_szdrhwiq.json"):
            st_lottie(lottie_feedback, height=300)

def register_page():
    st.title("📝 Student Registration")
    
    with st.form("registration_form"):
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name")
            username = st.text_input("Choose Username")
        with col2:
            reg_number = st.text_input("Registration Number")
            room_number = st.text_input("Room Number")
        
        email = st.text_input("College Email")
        password = st.text_input("Create Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Register Account"):
            if not all([full_name, username, reg_number, room_number, email, password, confirm_pass]):
                st.error("Please fill in all fields!")
            elif password != confirm_pass:
                st.error("Passwords don't match!")
            else:
                user_data = {
                    'name': full_name,
                    'email': email,
                    'reg_no': reg_number,
                    'room_no': room_number
                }
                success, message = register_user(username, password, user_data)
                if success:
                    st.success(message + " Please login.")
                    st.info("Redirecting to login page...")
                    time.sleep(2)
                    st.session_state.show_login = True
                    st.rerun()
                else:
                    st.error(message)

def feedback_page():
    if not st.session_state.get('logged_in'):
        st.warning("Please login first")
        return
    
    st.title("📝 Submit Feedback")
    st.write(f"Welcome back, {st.session_state.current_user}!")
    
    with st.form("feedback_form"):
        st.subheader("Hostel Facilities")
        hostel_feedback = st.text_area("Comments about hostel")
        hostel_rating = st.selectbox("Overall Rating", ["A", "B", "C", "D", "E"])
        
        st.subheader("Mess Food Quality")
        mess_type = st.radio("Food Type", ["Veg", "Non-Veg", "Special","Food-Park"])
        mess_feedback = st.text_area("Comments about mess food")
        mess_rating = st.selectbox("Food Rating", ["A", "B", "C", "D", "E"])
        
        st.subheader("Bathroom Cleanliness")
        bathroom_feedback = st.text_area("Bathroom comments")
        bathroom_rating = st.selectbox("Cleanliness Rating", ["A", "B", "C", "D", "E"])
        
        other_comments = st.text_area("Other suggestions")
        
        if st.form_submit_button("Submit Feedback", type="primary"):
            feedback_data = {
                'hostel_feedback': hostel_feedback,
                'hostel_rating': hostel_rating,
                'mess_feedback': mess_feedback,
                'mess_type': mess_type,
                'mess_rating': mess_rating,
                'bathroom_feedback': bathroom_feedback,
                'bathroom_rating': bathroom_rating,
                'other_comments': other_comments
            }
            if submit_feedback(st.session_state.current_user, feedback_data):
                st.success("Thank you for your feedback!")
                st.balloons()
            else:
                st.error("Failed to submit feedback. Please try again.")

def faq_page():
    st.title("❓ Frequently Asked Questions")
    
    with st.expander("How do I submit feedback?"):
        st.write("After logging in, go to 'Submit Feedback' and fill out the form.")
    
    with st.expander("What do the ratings mean?"):
        st.write("""
        - A: Excellent
        - B: Good
        - C: Average
        - D: Below average
        - E: Poor
        """)
    
    with st.expander("Who can view my feedback?"):
        st.write("Only authorized administrators can view feedback with strict confidentiality.")

# ======================
# ADMIN PAGES
# ======================
def admin_dashboard():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("📊 Admin Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Users", get_user_count())
        st.metric("Total Feedback", get_feedback_count())
        
    with col2:
        if lottie_admin := load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_hu9uedjd.json"):
            st_lottie(lottie_admin, height=200)
    
    st.subheader("Recent Feedback")
    recent_feedback = get_recent_feedback()
    if not recent_feedback.empty:
        st.dataframe(recent_feedback, hide_index=True)
    else:
        st.info("No feedback yet")

def feedback_viewer():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("🔍 Feedback Records")
    
    feedback_data = get_all_feedback()
    if feedback_data.empty:
        st.info("No feedback submissions yet")
        return
    
    st.dataframe(feedback_data)
    
    st.download_button(
        "Export as CSV",
        feedback_data.to_csv(index=False),
        "hostel_feedback.csv",
        "text/csv"
    )

def user_manager():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("👥 User Management")
    
    users_data = get_all_users()
    if users_data.empty:
        st.info("No users registered yet")
        return
    
    st.dataframe(users_data)
    
    st.subheader("User Actions")
    usernames = users_data['username'].tolist()
    if usernames:
        delete_username = st.selectbox("Select user to remove", usernames)
        
        if st.button("Delete User", type="primary"):
            if delete_user(delete_username):
                log_admin_action("USER_DELETION", f"Deleted user: {delete_username}")
                st.success(f"User {delete_username} removed")
                st.rerun()
            else:
                st.error("Failed to delete user")

def system_logs():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("📜 System Logs")
    
    logs_data = get_admin_logs()
    if logs_data.empty:
        st.info("No system logs yet")
        return
    
    st.dataframe(logs_data)
    
    if st.button("Clear Logs", type="secondary"):
        if clear_admin_logs():
            st.success("Logs cleared successfully")
            st.rerun()
        else:
            st.error("Failed to clear logs")

# ======================
# APPLICATION ENTRY
# ======================
if __name__ == "__main__":
    main()
