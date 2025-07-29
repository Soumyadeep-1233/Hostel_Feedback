# Hostel Feedback System with Admin Controls
# Streamlit Application - Complete Code

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import hashlib
from streamlit_lottie import st_lottie
import requests
import json

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
# SECURITY SETTINGS
# ======================
# ADMIN CREDENTIALS [CHANGE THESE IN PRODUCTION]
ADMIN_USERNAME = "hostel_admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("SecureAdminPass123!".encode()).hexdigest()

# ======================
# HELPER FUNCTIONS
# ======================
def hash_password(password):
    """Securely hash passwords using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_lottieurl(url):
    """Load Lottie animations from URL"""
    r = requests.get(url)
    return None if r.status_code != 200 else r.json()

def init_databases():
    """Initialize data storage"""
    if 'users_db' not in st.session_state:
        st.session_state.users_db = pd.DataFrame(columns=[
            'username', 'password', 'name', 'email', 
            'reg_no', 'room_no', 'last_login'
        ])
    
    if 'feedback_db' not in st.session_state:
        st.session_state.feedback_db = pd.DataFrame(columns=[
            'username', 'timestamp', 'hostel_feedback', 'hostel_rating',
            'mess_feedback', 'mess_type', 'mess_rating',
            'bathroom_feedback', 'bathroom_rating', 'other_comments'
        ])
    
    if 'admin_logs' not in st.session_state:
        st.session_state.admin_logs = pd.DataFrame(columns=[
            'timestamp', 'action', 'details'
        ])

def log_admin_action(action, details=""):
    """Record admin activities"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame({
        'timestamp': [timestamp],
        'action': [action],
        'details': [details]
    })
    st.session_state.admin_logs = pd.concat(
        [st.session_state.admin_logs, new_log], 
        ignore_index=True
    )

# ======================
# AUTHENTICATION FUNCTIONS
# ======================
def authenticate_admin(username, password):
    """Verify admin credentials"""
    return (username == ADMIN_USERNAME and 
            hash_password(password) == ADMIN_PASSWORD_HASH)

def authenticate_user(username, password):
    """Verify student credentials"""
    user = st.session_state.users_db[
        (st.session_state.users_db['username'] == username) & 
        (st.session_state.users_db['password'] == hash_password(password))
    ]
    if not user.empty:
        st.session_state.users_db.loc[
            st.session_state.users_db['username'] == username, 
            'last_login'
        ] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    return False

def register_user(username, password, user_data):
    """Register new student"""
    if username in st.session_state.users_db['username'].values:
        return False, "Username already exists"
    
    new_user = pd.DataFrame({
        'username': [username],
        'password': [hash_password(password)],
        **user_data
    })
    
    st.session_state.users_db = pd.concat(
        [st.session_state.users_db, new_user], 
        ignore_index=True
    )
    return True, "Registration successful"

# ======================
# FEEDBACK FUNCTIONS
# ======================
def submit_feedback(username, feedback_data):
    """Submit new feedback"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_feedback = pd.DataFrame({
        'username': [username],
        'timestamp': [timestamp],
        **feedback_data
    })
    st.session_state.feedback_db = pd.concat(
        [st.session_state.feedback_db, new_feedback], 
        ignore_index=True
    )
    return True

# ======================
# UI COMPONENTS
# ======================
def show_admin_sidebar():
    """Admin-specific sidebar options"""
    st.sidebar.header("Admin Controls")
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout Admin", type="primary"):
        st.session_state.clear()
        st.rerun()

def show_user_sidebar():
    """Regular user sidebar options"""
    st.sidebar.header(f"Welcome {st.session_state.current_user}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
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
    # Initialize databases
    init_databases()
    
    # Load animations
    lottie_feedback = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_szdrhwiq.json")
    lottie_admin = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_hu9uedjd.json")

    # Sidebar Navigation
    st.sidebar.title("Hostel Feedback System")
    
    # Show appropriate sidebar based on login state
    if st.session_state.get('is_admin'):
        show_admin_sidebar()
    elif st.session_state.get('logged_in'):
        show_user_sidebar()
    
    # Navigation options
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
    
    page = st.sidebar.selectbox("Menu", list(pages.keys()))
    pages[page]()

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
        - Rate mess food quality (Veg/Non-Veg/Special)
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
            if password != confirm_pass:
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
                    time.sleep(2)
                    st.switch_page("main.py?page=Login")
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
        mess_type = st.radio("Food Type", ["Veg", "Non-Veg", "Special Diet"])
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
            submit_feedback(st.session_state.current_user, feedback_data)
            st.success("Thank you for your feedback!")
            st.balloons()

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
        st.metric("Total Users", len(st.session_state.users_db))
        st.metric("Total Feedback", len(st.session_state.feedback_db))
        
    with col2:
        if lottie_admin := load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_hu9uedjd.json"):
            st_lottie(lottie_admin, height=200)
    
    st.subheader("Recent Feedback")
    if not st.session_state.feedback_db.empty:
        st.dataframe(
            st.session_state.feedback_db.sort_values('timestamp', ascending=False).head(5),
            hide_index=True
        )
    else:
        st.info("No feedback yet")

def feedback_viewer():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("🔍 Feedback Records")
    
    if st.session_state.feedback_db.empty:
        st.info("No feedback submissions yet")
        return
    
    st.dataframe(st.session_state.feedback_db)
    
    st.download_button(
        "Export as CSV",
        st.session_state.feedback_db.to_csv(),
        "hostel_feedback.csv",
        "text/csv"
    )

def user_manager():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("👥 User Management")
    
    st.dataframe(st.session_state.users_db.drop(columns=['password']))
    
    st.subheader("User Actions")
    delete_user = st.selectbox(
        "Select user to remove",
        st.session_state.users_db['username'].values
    )
    
    if st.button("Delete User", type="primary"):
        st.session_state.users_db = st.session_state.users_db[
            st.session_state.users_db['username'] != delete_user
        ]
        log_admin_action("USER_DELETION", f"Deleted user: {delete_user}")
        st.success(f"User {delete_user} removed")
        st.rerun()

def system_logs():
    if not st.session_state.get('is_admin'):
        st.warning("Unauthorized access")
        return
    
    st.title("📜 System Logs")
    st.dataframe(st.session_state.admin_logs)
    
    if st.button("Clear Logs", type="secondary"):
        st.session_state.admin_logs = pd.DataFrame(columns=[
            'timestamp', 'action', 'details'
        ])
        st.rerun()

# ======================
# APPLICATION ENTRY
# ======================
if __name__ == "__main__":
    main()

