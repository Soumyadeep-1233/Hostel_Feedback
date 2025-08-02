# Hostel Feedback System with Admin Controls
# Streamlit Application - Complete Code with LinkedIn Compatibility

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import hashlib
import requests
import json

# ======================
# CONFIGURATION & SEO
# ======================
st.set_page_config(
    page_title="Hostel Feedback System - Student Portal",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'Report a bug': None,
        'About': "Hostel Feedback Management System for Students"
    }
)

# Check if this is a social media crawler
def detect_crawler():
    """Detect if the request is from a social media crawler"""
    try:
        # Check query params for crawler indicators
        query_params = st.experimental_get_query_params()
        
        # Check common crawler parameters
        if any(key in query_params for key in ['_escaped_fragment_', 'crawl', 'bot']):
            return True
            
        # If we can detect user agent from headers (not always available in Streamlit)
        return False
    except:
        return False

# Serve static content for crawlers
if detect_crawler():
    st.markdown("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hostel Feedback System - Student Portal</title>
        <meta property="og:title" content="Hostel Feedback Management System" />
        <meta property="og:description" content="Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality management." />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=1200&h=630&fit=crop" />
        <meta name="description" content="Student feedback system for hostel facilities, mess food quality, and accommodation services." />
    </head>
    <body>
        <h1>Hostel Feedback Management System</h1>
        <p>Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality.</p>
        <p>Features: Secure registration, feedback submission, administrative dashboard, real-time analytics.</p>
    </body>
    </html>
    """, unsafe_allow_html=True)
    st.stop()

# ======================
# SECURITY SETTINGS
# ======================
# ADMIN CREDENTIALS [CHANGE THESE IN PRODUCTION]
ADMIN_USERNAME = "hostel_admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Soumya@1234".encode()).hexdigest()

# ======================
# HELPER FUNCTIONS
# ======================
def hash_password(password):
    """Securely hash passwords using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_lottie_safe(url):
    """Safely load Lottie animations with error handling"""
    try:
        r = requests.get(url, timeout=5)
        return None if r.status_code != 200 else r.json()
    except Exception:
        return None

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
    
    # Initialize session state variables for login persistence
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

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
# PAGE COMPONENTS
# ======================
def home_page():
    # Serve static HTML for crawlers first
    st.markdown("""
    <div style="display: none;" class="crawler-content">
        <h1>Hostel Feedback Management System</h1>
        <p>Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality management.</p>
        <p>Features include secure student registration, feedback submission with ratings, administrative dashboard, and real-time analytics.</p>
        <p>Students can rate hostel accommodation, mess food quality (Veg/Non-Veg/Special/Food-Park), bathroom cleanliness, and provide suggestions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Regular content for users
    st.title("🏠 Hostel Feedback Management System")
    st.subheader("Comprehensive Student Feedback Portal")
    
    # Static description for crawlers - must be visible text
    st.write("**Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality management.**")
    
    st.markdown("""
    ## Welcome to Our Hostel Feedback System
    
    **A comprehensive platform for students to share feedback about:**
    - Hostel accommodation facilities
    - Mess food quality (Vegetarian, Non-Vegetarian, Special meals)
    - Bathroom and hygiene standards
    - General suggestions for improvement
    
    ### Features:
    - ✅ Secure student registration and login
    - 📝 Easy feedback submission with ratings
    - 👨‍💼 Administrative dashboard for management
    - 📊 Real-time feedback analytics
    - 🔒 Data privacy and security
    """)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.info("**Please register or login to submit feedback**")
        
        # Quick stats (if data exists)
        if not st.session_state.feedback_db.empty:
            st.metric("Total Feedback Submissions", len(st.session_state.feedback_db))
        
        st.markdown("""
        ### How It Works:
        1. **Register** with your student details
        2. **Login** to access the feedback portal
        3. **Submit** detailed feedback with ratings
        4. **Help** improve hostel facilities for everyone
        """)
        
    with col2:
        # Simple fallback without external dependencies
        st.info("🏠 Hostel Feedback Portal")
        st.write("Submit feedback for:")
        st.write("• Hostel facilities")
        st.write("• Mess food quality")
        st.write("• Bathroom cleanliness")
        st.write("• General suggestions")

def register_page():
    st.title("📝 Student Registration")
    st.write("Create your account to start submitting feedback")
    
    with st.form("registration_form"):
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name*")
            username = st.text_input("Choose Username*")
        with col2:
            reg_number = st.text_input("Registration Number*")
            room_number = st.text_input("Room Number*")
        
        email = st.text_input("College Email*")
        password = st.text_input("Create Password*", type="password")
        confirm_pass = st.text_input("Confirm Password*", type="password")
        
        if st.form_submit_button("Register Account", type="primary"):
            if not all([full_name, username, reg_number, room_number, email, password, confirm_pass]):
                st.error("Please fill in all required fields marked with *")
            elif password != confirm_pass:
                st.error("Passwords don't match!")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                user_data = {
                    'name': [full_name],
                    'email': [email],
                    'reg_no': [reg_number],
                    'room_no': [room_number],
                    'last_login': [None]
                }
                success, message = register_user(username, password, user_data)
                if success:
                    st.success(message + " Please login now.")
                    st.info("Registration completed! Use the Login page to access your account.")
                else:
                    st.error(message)

def feedback_page():
    if not st.session_state.get('logged_in'):
        st.warning("Please login first to submit feedback")
        return
    
    st.title("📝 Submit Your Feedback")
    st.write(f"Welcome back, **{st.session_state.current_user}**!")
    
    with st.form("feedback_form"):
        st.subheader("🏠 Hostel Facilities")
        hostel_feedback = st.text_area("Share your thoughts about hostel facilities", 
                                     placeholder="Room conditions, common areas, WiFi, etc.")
        hostel_rating = st.selectbox("Overall Hostel Rating", 
                                   ["A (Excellent)", "B (Good)", "C (Average)", "D (Below Average)", "E (Poor)"])
        
        st.subheader("🍽️ Mess Food Quality")
        mess_type = st.radio("Food Type Today", ["Veg", "Non-Veg", "Special", "Food-Park"])
        mess_feedback = st.text_area("Comments about mess food", 
                                   placeholder="Taste, quantity, hygiene, variety, etc.")
        mess_rating = st.selectbox("Food Quality Rating", 
                                 ["A (Excellent)", "B (Good)", "C (Average)", "D (Below Average)", "E (Poor)"])
        
        st.subheader("🚿 Bathroom & Hygiene")
        bathroom_feedback = st.text_area("Bathroom cleanliness feedback", 
                                       placeholder="Cleanliness, maintenance, supplies, etc.")
        bathroom_rating = st.selectbox("Hygiene Rating", 
                                     ["A (Excellent)", "B (Good)", "C (Average)", "D (Below Average)", "E (Poor)"])
        
        st.subheader("💭 Additional Suggestions")
        other_comments = st.text_area("Any other suggestions or concerns", 
                                    placeholder="Security, recreation, study areas, etc.")
        
        if st.form_submit_button("Submit Feedback", type="primary"):
            feedback_data = {
                'hostel_feedback': [hostel_feedback],
                'hostel_rating': [hostel_rating.split()[0]],  # Extract letter grade
                'mess_feedback': [mess_feedback],
                'mess_type': [mess_type],
                'mess_rating': [mess_rating.split()[0]],  # Extract letter grade
                'bathroom_feedback': [bathroom_feedback],
                'bathroom_rating': [bathroom_rating.split()[0]],  # Extract letter grade
                'other_comments': [other_comments]
            }
            
            if submit_feedback(st.session_state.current_user, feedback_data):
                st.success("✅ Thank you for your valuable feedback!")
                st.balloons()
                st.info("Your feedback helps us improve hostel services for everyone.")

def faq_page():
    st.title("❓ Frequently Asked Questions")
    st.write("Find answers to common questions about the feedback system")
    
    with st.expander("How do I submit feedback?", expanded=True):
        st.write("""
        1. **Register** an account with your student details
        2. **Login** using your credentials
        3. Navigate to **Submit Feedback**
        4. Fill out the feedback form with your comments and ratings
        5. Click **Submit** to send your feedback
        """)
    
    with st.expander("What do the rating grades mean?"):
        st.write("""
        **Rating Scale:**
        - **A (Excellent)**: Outstanding quality, no issues
        - **B (Good)**: Above average, minor improvements needed
        - **C (Average)**: Acceptable but room for improvement
        - **D (Below Average)**: Significant issues, needs attention
        - **E (Poor)**: Major problems, immediate action required
        """)
    
    with st.expander("Is my feedback confidential?"):
        st.write("""
        Yes, your feedback is handled with strict confidentiality:
        - Only authorized administrators can view submissions
        - Personal information is protected
        - Feedback is used solely for facility improvement
        - No individual responses are shared publicly
        """)
    
    with st.expander("How often can I submit feedback?"):
        st.write("You can submit feedback as often as needed. We encourage regular submissions to help us maintain and improve services.")
    
    with st.expander("What happens after I submit feedback?"):
        st.write("""
        1. Your feedback is immediately stored in our system
        2. Administrative team reviews all submissions regularly
        3. Issues are prioritized based on frequency and severity
        4. Improvements are implemented where possible
        5. Major changes may be communicated to all residents
        """)

# ======================
# ADMIN PAGES
# ======================
def admin_dashboard():
    if not st.session_state.get('is_admin'):
        st.warning("⚠️ Unauthorized access - Admin login required")
        return
    
    st.title("📊 Administrative Dashboard")
    st.write("Comprehensive overview of hostel feedback system")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Users", len(st.session_state.users_db))
    with col2:
        st.metric("📝 Total Feedback", len(st.session_state.feedback_db))
    with col3:
        if not st.session_state.feedback_db.empty:
            recent_feedback = len(st.session_state.feedback_db[
                pd.to_datetime(st.session_state.feedback_db['timestamp']) >= 
                pd.Timestamp.now() - pd.Timedelta(days=7)
            ])
            st.metric("📅 This Week", recent_feedback)
        else:
            st.metric("📅 This Week", 0)
    with col4:
        if not st.session_state.admin_logs.empty:
            st.metric("📜 System Logs", len(st.session_state.admin_logs))
        else:
            st.metric("📜 System Logs", 0)
    
    # Recent Activity
    st.subheader("🕒 Recent Feedback Submissions")
    if not st.session_state.feedback_db.empty:
        recent_df = st.session_state.feedback_db.sort_values('timestamp', ascending=False).head(10)
        st.dataframe(recent_df[['username', 'timestamp', 'hostel_rating', 'mess_rating', 'bathroom_rating']], 
                    use_container_width=True)
    else:
        st.info("No feedback submissions yet")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 View All Feedback", type="secondary"):
            st.session_state.current_page = "View Feedback"
            st.rerun()
    with col2:
        if st.button("👥 Manage Users", type="secondary"):
            st.session_state.current_page = "User Management"
            st.rerun()
    with col3:
        if st.button("📜 System Logs", type="secondary"):
            st.session_state.current_page = "System Logs"
            st.rerun()

def feedback_viewer():
    if not st.session_state.get('is_admin'):
        st.warning("⚠️ Unauthorized access - Admin login required")
        return
    
    st.title("🔍 Feedback Records & Analytics")
    
    if st.session_state.feedback_db.empty:
        st.info("📭 No feedback submissions yet")
        return
    
    # Feedback filters
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("Filter by date (optional)")
    with col2:
        rating_filter = st.selectbox("Filter by rating", ["All", "A", "B", "C", "D", "E"])
    
    # Apply filters
    filtered_df = st.session_state.feedback_db.copy()
    if rating_filter != "All":
        filtered_df = filtered_df[
            (filtered_df['hostel_rating'] == rating_filter) |
            (filtered_df['mess_rating'] == rating_filter) |
            (filtered_df['bathroom_rating'] == rating_filter)
        ]
    
    st.subheader("📋 All Feedback Submissions")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # Export functionality
    st.subheader("📤 Export Data")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Download as CSV",
            csv_data,
            f"hostel_feedback_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            type="primary"
        )
    with col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()

def user_manager():
    if not st.session_state.get('is_admin'):
        st.warning("⚠️ Unauthorized access - Admin login required")
        return
    
    st.title("👥 User Management")
    
    if st.session_state.users_db.empty:
        st.info("📭 No users registered yet")
        return
    
    st.subheader("📊 Registered Users")
    # Display users without password column
    display_df = st.session_state.users_db.drop(columns=['password'])
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.subheader("🛠️ User Management Actions")
    if len(st.session_state.users_db) > 0:
        delete_user = st.selectbox(
            "Select user to remove",
            ["Select a user..."] + list(st.session_state.users_db['username'].values)
        )
        
        if delete_user != "Select a user...":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete User", type="primary"):
                    # Remove user
                    st.session_state.users_db = st.session_state.users_db[
                        st.session_state.users_db['username'] != delete_user
                    ]
                    # Remove their feedback too
                    st.session_state.feedback_db = st.session_state.feedback_db[
                        st.session_state.feedback_db['username'] != delete_user
                    ]
                    log_admin_action("USER_DELETION", f"Deleted user: {delete_user}")
                    st.success(f"User {delete_user} removed successfully")
                    st.rerun()
            with col2:
                st.warning("⚠️ This action cannot be undone")

def system_logs():
    if not st.session_state.get('is_admin'):
        st.warning("⚠️ Unauthorized access - Admin login required")
        return
    
    st.title("📜 System Activity Logs")
    
    if st.session_state.admin_logs.empty:
        st.info("📭 No system logs yet")
        return
    
    st.subheader("🕒 Recent Administrative Actions")
    # Sort logs by timestamp (most recent first)
    sorted_logs = st.session_state.admin_logs.sort_values('timestamp', ascending=False)
    st.dataframe(sorted_logs, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear All Logs", type="secondary"):
            st.session_state.admin_logs = pd.DataFrame(columns=[
                'timestamp', 'action', 'details'
            ])
            log_admin_action("LOGS_CLEARED", "All previous logs cleared")
            st.success("System logs cleared")
            st.rerun()
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()

# ======================
# MAIN APPLICATION
# ======================
def main():
    # Initialize databases and session state
    init_databases()
    
    # Immediately display static content for crawlers
    st.markdown("""
    <div style="visibility: hidden; height: 0;">
        <h1>Hostel Feedback Management System</h1>
        <p>Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality management.</p>
        <p>Features: Secure student registration, feedback submission with ratings, administrative dashboard, real-time analytics.</p>
        <p>Students can submit feedback about hostel accommodation, mess food quality (Vegetarian, Non-Vegetarian, Special meals, Food-Park), bathroom cleanliness, and general suggestions for improvement.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show debug info only in development
    if st.sidebar.checkbox("🔧 Debug Mode", value=False):
        st.sidebar.write("**Session State:**")
        st.sidebar.write(f"Logged in: {st.session_state.get('logged_in', False)}")
        st.sidebar.write(f"Current user: {st.session_state.get('current_user', 'None')}")
        st.sidebar.write(f"Is admin: {st.session_state.get('is_admin', False)}")
    
    # Sidebar Navigation
    st.sidebar.title("🏠 Hostel Portal")
    
    # Show appropriate sidebar based on login state
    if st.session_state.get('is_admin'):
        show_admin_sidebar()
    elif st.session_state.get('logged_in'):
        show_user_sidebar()
    else:
        st.sidebar.info("ℹ️ Login to access all features")
    
    # Navigation options based on authentication status
    if st.session_state.get('is_admin'):
        pages = {
            "📊 Dashboard": admin_dashboard,
            "🔍 View Feedback": feedback_viewer,
            "👥 User Management": user_manager,
            "📜 System Logs": system_logs
        }
        st.sidebar.success("🔑 Admin Access")
    elif st.session_state.get('logged_in'):
        pages = {
            "🏠 Home": home_page,
            "📝 Submit Feedback": feedback_page,
            "❓ FAQ": faq_page
        }
        st.sidebar.success(f"👋 Welcome {st.session_state.current_user}")
    else:
        pages = {
            "🏠 Home": home_page,
            "📝 Register": register_page,
            "🔒 Login": render_login_page,
            "❓ FAQ": faq_page
        }
    
    # Handle page selection
    page = st.sidebar.selectbox("📋 Navigation", list(pages.keys()), key="page_selector")
    
    # Execute the selected page function with error handling
    try:
        pages[page]()
    except Exception as e:
        st.error(f"⚠️ Application Error: {str(e)}")
        st.info("Please try refreshing the page or contact system administrator.")
        # Log error for admin
        if st.session_state.get('is_admin'):
            log_admin_action("ERROR", f"Page: {page}, Error: {str(e)}")

# Add footer with contact information
def add_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Hostel Feedback Management System</strong></p>
        <p>For technical support or inquiries, contact your hostel administration.</p>
        <p><small>© 2024 Student Portal - Secure & Confidential</small></p>
    </div>
    """, unsafe_allow_html=True)

# ======================
# APPLICATION ENTRY
# ======================
if __name__ == "__main__":
    # Add robots.txt content for crawlers
    st.markdown("""
    <script>
    // Add meta tags dynamically for social crawlers
    if (document.querySelector('meta[property="og:title"]') === null) {
        const metaTags = [
            {property: "og:title", content: "Hostel Feedback Management System"},
            {property: "og:description", content: "Comprehensive student feedback portal for hostel facilities, mess services, and accommodation quality."},
            {property: "og:type", content: "website"},
            {property: "og:image", content: "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=1200&h=630&fit=crop"},
            {name: "description", content: "Student feedback system for hostel facilities, mess food quality, and accommodation services."},
            {name: "robots", content: "index, follow"}
        ];
        
        metaTags.forEach(tag => {
            const meta = document.createElement('meta');
            if (tag.property) meta.setAttribute('property', tag.property);
            if (tag.name) meta.setAttribute('name', tag.name);
            meta.setAttribute('content', tag.content);
            document.head.appendChild(meta);
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    main()
    add_footer()
