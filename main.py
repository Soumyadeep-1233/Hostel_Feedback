# Hostel Feedback System with SQLite Database
# Streamlit Application - Complete Code with Enhanced Admin Feedback Views

import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime
import hashlib
from streamlit_lottie import st_lottie
# Removed matplotlib and seaborn imports - not available in Streamlit Cloud

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
ADMIN_PASSWORD_HASH = hashlib.sha256("Soumya@1234".encode()).hexdigest()

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

def get_hostel_feedback():
    """Get hostel-specific feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT username, timestamp, hostel_feedback, hostel_rating, other_comments
                FROM feedback 
                WHERE hostel_feedback IS NOT NULL AND hostel_feedback != ''
                ORDER BY timestamp DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting hostel feedback: {e}")
    return pd.DataFrame()

def get_mess_feedback():
    """Get mess-specific feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT username, timestamp, mess_feedback, mess_type, mess_rating, other_comments
                FROM feedback 
                WHERE mess_feedback IS NOT NULL AND mess_feedback != ''
                ORDER BY timestamp DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting mess feedback: {e}")
    return pd.DataFrame()

def get_bathroom_feedback():
    """Get bathroom-specific feedback entries"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT username, timestamp, bathroom_feedback, bathroom_rating, other_comments
                FROM feedback 
                WHERE bathroom_feedback IS NOT NULL AND bathroom_feedback != ''
                ORDER BY timestamp DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting bathroom feedback: {e}")
    return pd.DataFrame()

def get_rating_statistics(rating_type):
    """Get rating statistics for visualization"""
    try:
        with get_db_connection() as connection:
            if connection:
                cursor = connection.cursor()
                query = f"""
                SELECT {rating_type}_rating as rating, COUNT(*) as count
                FROM feedback 
                GROUP BY {rating_type}_rating
                ORDER BY rating
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
                return pd.DataFrame(data)
    except sqlite3.Error as e:
        st.error(f"Error getting rating statistics: {e}")
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

def create_rating_chart(data, title):
    """Create rating distribution chart using Streamlit native charts"""
    if data.empty:
        return None
    
    # Create a bar chart using streamlit
    st.subheader(f"{title} Rating Distribution")
    
    # Display as columns with metrics
    cols = st.columns(len(data))
    for idx, (_, row) in enumerate(data.iterrows()):
        with cols[idx]:
            # Color coding for ratings
            if row['rating'] == 'A':
                st.success(f"**{row['rating']}** - {int(row['count'])}")
            elif row['rating'] == 'B':
                st.info(f"**{row['rating']}** - {int(row['count'])}")
            elif row['rating'] == 'C':
                st.warning(f"**{row['rating']}** - {int(row['count'])}")
            elif row['rating'] in ['D', 'E']:
                st.error(f"**{row['rating']}** - {int(row['count'])}")
    
    # Display as bar chart
    chart_data = data.set_index('rating')
    st.bar_chart(chart_data)

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
            "Hostel Feedback": hostel_feedback_viewer,
            "Mess Feedback": mess_feedback_viewer,
            "Bathroom Feedback": bathroom_feedback_viewer,
            "All Feedback": feedback_viewer,
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

def hostel_feedback_viewer():
    """View hostel-specific feedback"""
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("🏠 Hostel Feedback Analysis")
    log_admin_action("VIEWED_HOSTEL_FEEDBACK")
    
    hostel_data = get_hostel_feedback()
    
    if hostel_data.empty:
        st.info("No hostel feedback submissions yet")
        return
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Hostel Feedback", len(hostel_data))
    with col2:
        avg_rating = hostel_data['hostel_rating'].mode().iloc[0] if not hostel_data.empty else 'N/A'
        st.metric("Most Common Rating", avg_rating)
    with col3:
        latest_feedback = hostel_data['timestamp'].max() if not hostel_data.empty else 'N/A'
        st.metric("Latest Feedback", latest_feedback.split('T')[0] if latest_feedback != 'N/A' else 'N/A')
    
    # Rating Distribution Chart
    rating_stats = get_rating_statistics('hostel')
    if not rating_stats.empty:
        create_rating_chart(rating_stats, "Hostel")
    
    # Detailed Feedback Table
    st.subheader("Detailed Hostel Feedback")
    
    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        rating_filter = st.selectbox("Filter by Rating", ['All'] + ['A', 'B', 'C', 'D', 'E'])
    with col2:
        search_term = st.text_input("Search in feedback")
    
    # Apply filters
    filtered_data = hostel_data.copy()
    if rating_filter != 'All':
        filtered_data = filtered_data[filtered_data['hostel_rating'] == rating_filter]
    if search_term:
        filtered_data = filtered_data[
            filtered_data['hostel_feedback'].str.contains(search_term, case=False, na=False)
        ]
    
    st.dataframe(
        filtered_data,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date & Time"),
            "hostel_feedback": st.column_config.TextColumn("Feedback", width="large"),
            "hostel_rating": st.column_config.SelectboxColumn("Rating"),
        },
        hide_index=True
    )
    
    # Export option
    if not filtered_data.empty:
        st.download_button(
            "📥 Export Hostel Feedback as CSV",
            filtered_data.to_csv(index=False),
            "hostel_feedback.csv",
            "text/csv"
        )

def mess_feedback_viewer():
    """View mess-specific feedback"""
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("🍽️ Mess Feedback Analysis")
    log_admin_action("VIEWED_MESS_FEEDBACK")
    
    mess_data = get_mess_feedback()
    
    if mess_data.empty:
        st.info("No mess feedback submissions yet")
        return
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Mess Feedback", len(mess_data))
    with col2:
        avg_rating = mess_data['mess_rating'].mode().iloc[0] if not mess_data.empty else 'N/A'
        st.metric("Most Common Rating", avg_rating)
    with col3:
        popular_type = mess_data['mess_type'].mode().iloc[0] if not mess_data.empty else 'N/A'
        st.metric("Popular Mess Type", popular_type)
    with col4:
        latest_feedback = mess_data['timestamp'].max() if not mess_data.empty else 'N/A'
        st.metric("Latest Feedback", latest_feedback.split('T')[0] if latest_feedback != 'N/A' else 'N/A')
    
    # Rating Distribution Chart
    rating_stats = get_rating_statistics('mess')
    if not rating_stats.empty:
        create_rating_chart(rating_stats, "Mess")
    
    # Mess Type Distribution
    st.subheader("Mess Type Distribution")
    mess_type_counts = mess_data['mess_type'].value_counts()
    if not mess_type_counts.empty:
        col1, col2 = st.columns(2)
        with col1:
            for mess_type, count in mess_type_counts.items():
                st.metric(mess_type, count)
        with col2:
            st.bar_chart(mess_type_counts)
    
    # Detailed Feedback Table
    st.subheader("Detailed Mess Feedback")
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        rating_filter = st.selectbox("Filter by Rating", ['All'] + ['A', 'B', 'C', 'D', 'E'])
    with col2:
        type_filter = st.selectbox("Filter by Mess Type", ['All'] + ['Veg', 'Non-Veg', 'Special', 'Food-Park'])
    with col3:
        search_term = st.text_input("Search in feedback")
    
    # Apply filters
    filtered_data = mess_data.copy()
    if rating_filter != 'All':
        filtered_data = filtered_data[filtered_data['mess_rating'] == rating_filter]
    if type_filter != 'All':
        filtered_data = filtered_data[filtered_data['mess_type'] == type_filter]
    if search_term:
        filtered_data = filtered_data[
            filtered_data['mess_feedback'].str.contains(search_term, case=False, na=False)
        ]
    
    st.dataframe(
        filtered_data,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date & Time"),
            "mess_feedback": st.column_config.TextColumn("Feedback", width="large"),
            "mess_type": st.column_config.SelectboxColumn("Mess Type"),
            "mess_rating": st.column_config.SelectboxColumn("Rating"),
        },
        hide_index=True
    )
    
    # Export option
    if not filtered_data.empty:
        st.download_button(
            "📥 Export Mess Feedback as CSV",
            filtered_data.to_csv(index=False),
            "mess_feedback.csv",
            "text/csv"
        )

def bathroom_feedback_viewer():
    """View bathroom-specific feedback"""
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("🚿 Bathroom Feedback Analysis")
    log_admin_action("VIEWED_BATHROOM_FEEDBACK")
    
    bathroom_data = get_bathroom_feedback()
    
    if bathroom_data.empty:
        st.info("No bathroom feedback submissions yet")
        return
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bathroom Feedback", len(bathroom_data))
    with col2:
        avg_rating = bathroom_data['bathroom_rating'].mode().iloc[0] if not bathroom_data.empty else 'N/A'
        st.metric("Most Common Rating", avg_rating)
    with col3:
        latest_feedback = bathroom_data['timestamp'].max() if not bathroom_data.empty else 'N/A'
        st.metric("Latest Feedback", latest_feedback.split('T')[0] if latest_feedback != 'N/A' else 'N/A')
    
    # Rating Distribution Chart
    rating_stats = get_rating_statistics('bathroom')
    if not rating_stats.empty:
        create_rating_chart(rating_stats, "Bathroom")
    
    # Detailed Feedback Table
    st.subheader("Detailed Bathroom Feedback")
    
    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        rating_filter = st.selectbox("Filter by Rating", ['All'] + ['A', 'B', 'C', 'D', 'E'])
    with col2:
        search_term = st.text_input("Search in feedback")
    
    # Apply filters
    filtered_data = bathroom_data.copy()
    if rating_filter != 'All':
        filtered_data = filtered_data[filtered_data['bathroom_rating'] == rating_filter]
    if search_term:
        filtered_data = filtered_data[
            filtered_data['bathroom_feedback'].str.contains(search_term, case=False, na=False)
        ]
    
    st.dataframe(
        filtered_data,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date & Time"),
            "bathroom_feedback": st.column_config.TextColumn("Feedback", width="large"),
            "bathroom_rating": st.column_config.SelectboxColumn("Rating"),
        },
        hide_index=True
    )
    
    # Export option
    if not filtered_data.empty:
        st.download_button(
            "📥 Export Bathroom Feedback as CSV",
            filtered_data.to_csv(index=False),
            "bathroom_feedback.csv",
            "text/csv"
        )

def feedback_viewer():
    """View all feedback entries (original function with enhancements)"""
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("📋 Complete Feedback Records")
    log_admin_action("VIEWED_ALL_FEEDBACK")
    
    feedback_data = get_all_feedback()
    if feedback_data.empty:
        st.info("No feedback submissions yet")
        return
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Feedback", len(feedback_data))
    with col2:
        unique_users = feedback_data['username'].nunique()
        st.metric("Active Users", unique_users)
    with col3:
        avg_hostel_rating = feedback_data['hostel_rating'].mode().iloc[0] if not feedback_data.empty else 'N/A'
        st.metric("Common Hostel Rating", avg_hostel_rating)
    with col4:
        avg_mess_rating = feedback_data['mess_rating'].mode().iloc[0] if not feedback_data.empty else 'N/A'
        st.metric("Common Mess Rating", avg_mess_rating)
    
    # Rating Comparison Section
    st.subheader("Rating Comparison Across Categories")
    
    # Display rating statistics for each category
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Hostel Ratings**")
        hostel_stats = get_rating_statistics('hostel')
        if not hostel_stats.empty:
            st.dataframe(hostel_stats, hide_index=True)
        else:
            st.info("No hostel ratings yet")
    
    with col2:
        st.write("**Mess Ratings**")
        mess_stats = get_rating_statistics('mess')
        if not mess_stats.empty:
            st.dataframe(mess_stats, hide_index=True)
        else:
            st.info("No mess ratings yet")
    
    with col3:
        st.write("**Bathroom Ratings**")
        bathroom_stats = get_rating_statistics('bathroom')
        if not bathroom_stats.empty:
            st.dataframe(bathroom_stats, hide_index=True)
        else:
            st.info("No bathroom ratings yet")
    
    # Advanced Filters
    st.subheader("Advanced Filtering")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_filter = st.date_input("Filter by Date (from)")
    with col2:
        username_filter = st.selectbox("Filter by User", ['All'] + feedback_data['username'].unique().tolist())
    with col3:
        mess_type_filter = st.selectbox("Filter by Mess Type", ['All'] + ['Veg', 'Non-Veg', 'Special', 'Food-Park'])
    with col4:
        overall_rating_filter = st.selectbox("Filter by Overall Rating", ['All'] + ['A', 'B', 'C', 'D', 'E'])
    
    # Apply advanced filters
    filtered_data = feedback_data.copy()
    
    if date_filter:
        filtered_data['date'] = pd.to_datetime(filtered_data['timestamp']).dt.date
        filtered_data = filtered_data[filtered_data['date'] >= date_filter]
    
    if username_filter != 'All':
        filtered_data = filtered_data[filtered_data['username'] == username_filter]
    
    if mess_type_filter != 'All':
        filtered_data = filtered_data[filtered_data['mess_type'] == mess_type_filter]
    
    if overall_rating_filter != 'All':
        filtered_data = filtered_data[
            (filtered_data['hostel_rating'] == overall_rating_filter) |
            (filtered_data['mess_rating'] == overall_rating_filter) |
            (filtered_data['bathroom_rating'] == overall_rating_filter)
        ]
    
    # Display filtered results
    st.subheader(f"Feedback Records ({len(filtered_data)} entries)")
    
    if not filtered_data.empty:
        st.dataframe(
            filtered_data,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Date & Time"),
                "hostel_feedback": st.column_config.TextColumn("Hostel Feedback", width="medium"),
                "mess_feedback": st.column_config.TextColumn("Mess Feedback", width="medium"),
                "bathroom_feedback": st.column_config.TextColumn("Bathroom Feedback", width="medium"),
                "other_comments": st.column_config.TextColumn("Other Comments", width="medium"),
            },
            hide_index=True
        )
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Export All Feedback as CSV",
                filtered_data.to_csv(index=False),
                "complete_feedback.csv",
                "text/csv"
            )
        with col2:
            # Summary report
            if st.button("📊 Generate Summary Report"):
                st.success("Summary Report Generated!")
                
                # Create summary
                summary_data = {
                    'Total Feedback Entries': len(filtered_data),
                    'Unique Users': filtered_data['username'].nunique(),
                    'Date Range': f"{filtered_data['timestamp'].min().split('T')[0]} to {filtered_data['timestamp'].max().split('T')[0]}",
                    'Most Common Hostel Rating': filtered_data['hostel_rating'].mode().iloc[0] if not filtered_data.empty else 'N/A',
                    'Most Common Mess Rating': filtered_data['mess_rating'].mode().iloc[0] if not filtered_data.empty else 'N/A',
                    'Most Common Bathroom Rating': filtered_data['bathroom_rating'].mode().iloc[0] if not filtered_data.empty else 'N/A',
                    'Most Popular Mess Type': filtered_data['mess_type'].mode().iloc[0] if not filtered_data.empty else 'N/A'
                }
                
                st.json(summary_data)

def user_manager():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("👥 User Management")
    log_admin_action("VIEWED_USER_MANAGEMENT")
    
    users_data = get_all_users()
    if users_data.empty:
        st.info("No users registered yet")
        return
    
    # User statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(users_data))
    with col2:
        active_users = users_data[users_data['last_login'].notna()]
        st.metric("Users with Login History", len(active_users))
    with col3:
        recent_users = len(users_data[pd.to_datetime(users_data['created_at']).dt.date >= pd.Timestamp.now().date() - pd.Timedelta(days=7)])
        st.metric("New Users (Last 7 days)", recent_users)
    
    # Users table
    st.subheader("User Directory")
    st.dataframe(
        users_data,
        column_config={
            "last_login": st.column_config.DatetimeColumn("Last Login"),
            "created_at": st.column_config.DatetimeColumn("Registration Date"),
        },
        hide_index=True
    )
    
    # User management actions
    st.subheader("User Actions")
    usernames = users_data['username'].tolist()
    if usernames:
        col1, col2 = st.columns(2)
        
        with col1:
            delete_username = st.selectbox("Select user to remove", usernames)
            
            if st.button("🗑️ Delete User", type="primary"):
                if delete_user(delete_username):
                    log_admin_action("USER_DELETION", f"Deleted user: {delete_username}")
                    st.success(f"User {delete_username} removed")
                    st.rerun()
                else:
                    st.error("Failed to delete user")
        
        with col2:
            st.download_button(
                "📥 Export User Data",
                users_data.to_csv(index=False),
                "users_data.csv",
                "text/csv"
            )

def system_logs():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("📜 System Logs")
    
    logs_data = get_admin_logs()
    if logs_data.empty:
        st.info("No system logs yet")
        return
    
    # Log statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Log Entries", len(logs_data))
    with col2:
        unique_actions = logs_data['action'].nunique()
        st.metric("Unique Actions", unique_actions)
    with col3:
        latest_log = logs_data['timestamp'].max() if not logs_data.empty else 'N/A'
        st.metric("Latest Activity", latest_log.split('T')[0] if latest_log != 'N/A' else 'N/A')
    
    # Action frequency
    st.subheader("Admin Actions Frequency")
    if not logs_data.empty:
        action_counts = logs_data['action'].value_counts()
        if not action_counts.empty:
            col1, col2 = st.columns(2)
            with col1:
                for action, count in action_counts.items():
                    st.metric(action, count)
            with col2:
                st.bar_chart(action_counts)
    
    # Logs table
    st.subheader("Detailed Logs")
    st.dataframe(
        logs_data,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date & Time"),
            "action": st.column_config.TextColumn("Action"),
            "details": st.column_config.TextColumn("Details", width="large"),
        },
        hide_index=True
    )
    
    # Log management
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear All Logs", type="secondary"):
            if clear_admin_logs():
                log_admin_action("LOGS_CLEARED", "All system logs cleared")
                st.success("Logs cleared successfully")
                st.rerun()
            else:
                st.error("Failed to clear logs")
    
    with col2:
        st.download_button(
            "📥 Export Logs as CSV",
            logs_data.to_csv(index=False),
            "system_logs.csv",
            "text/csv"
        )

# ======================
# APPLICATION ENTRY
# ======================
if __name__ == "__main__":
    main()
