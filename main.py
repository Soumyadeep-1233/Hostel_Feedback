# Hostel Feedback System with Admin Controls
# Streamlit Application - Complete Updated Code

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import hashlib
from streamlit_lottie import st_lottie
import requests

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
# ADMIN CREDENTIALS
ADMIN_USERNAME = "Soumyadeep"
ADMIN_PASSWORD_HASH = "aaf4c72dcbbc4f674cf1e7981d895f0c27319115e3006a51c93af4f5b9f8d003"  # SHA-256 of "Soumya@1234"

# ======================
# HELPER FUNCTIONS
# ======================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_lottieurl(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def init_databases():
    if 'users_db' not in st.session_state:
        st.session_state.users_db = pd.DataFrame(columns=[
            'username', 'password', 'name', 'email', 'reg_no', 'room_no'
        ])
    
    if 'feedback_db' not in st.session_state:
        st.session_state.feedback_db = pd.DataFrame(columns=[
            'username', 'timestamp', 'hostel_feedback', 'hostel_rating',
            'mess_feedback', 'mess_type', 'mess_rating',
            'bathroom_feedback', 'bathroom_rating', 'other_comments'
        ])

# ======================
# AUTHENTICATION
# ======================
def authenticate_admin(username, password):
    return (username == ADMIN_USERNAME and 
            hash_password(password) == ADMIN_PASSWORD_HASH)

def authenticate_user(username, password):
    user = st.session_state.users_db[
        (st.session_state.users_db['username'] == username) & 
        (st.session_state.users_db['password'] == hash_password(password))
    ]
    return not user.empty

def register_user(username, password, name, email, reg_no, room_no):
    if username in st.session_state.users_db['username'].values:
        return False, "Username already exists"
    
    new_user = pd.DataFrame({
        'username': [username],
        'password': [hash_password(password)],
        'name': [name],
        'email': [email],
        'reg_no': [reg_no],
        'room_no': [room_no]
    })
    
    st.session_state.users_db = pd.concat(
        [st.session_state.users_db, new_user], 
        ignore_index=True
    )
    return True, "Registration successful!"

# ======================
# MAIN APPLICATION
# ======================
def main():
    init_databases()
    
    # Load animations
    lottie_feedback = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_szdrhwiq.json")
    lottie_admin = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_hu9uedjd.json")

    # Navigation Setup
    st.sidebar.title("Hostel Feedback System")
    
    if st.session_state.get('is_admin'):
        menu = ["Admin Dashboard", "View Feedback", "User Management", "Logout"]
    elif st.session_state.get('logged_in'):
        menu = ["Home", "Submit Feedback", "FAQ", "Logout"]
    else:
        menu = ["Home", "Register", "Login", "FAQ"]
    
    choice = st.sidebar.selectbox("Menu", menu)

    # Pages
    if choice == "Home":
        st.title("🏠 Hostel Feedback Portal")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("""
            ### Welcome!
            This system allows students to:
            - Provide feedback about hostel facilities
            - Rate mess food quality
            - Report maintenance issues
            """)
        with col2:
            if lottie_feedback:
                st_lottie(lottie_feedback, height=200)
    
    elif choice == "Register":
        st.title("📝 Student Registration")
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            reg_no = st.text_input("Registration Number")
            room_no = st.text_input("Room Number")
            
            if st.form_submit_button("Register"):
                success, msg = register_user(username, password, name, email, reg_no, room_no)
                st.success(msg) if success else st.error(msg)
                if success:
                    time.sleep(1)
                    st.experimental_rerun()

    elif choice == "Login":
        st.title("🔐 Login")
        tab1, tab2 = st.tabs(["Student", "Admin"])
        
        with tab1:
            with st.form("student_login"):
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if authenticate_user(user, pwd):
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.success("Login successful!")
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("admin_login"):
                st.warning("Admin Access Only")
                admin_user = st.text_input("Admin Username")
                admin_pwd = st.text_input("Admin Password", type="password")
                if st.form_submit_button("Login as Admin"):
                    if authenticate_admin(admin_user, admin_pwd):
                        st.session_state.is_admin = True
                        st.session_state.logged_in = True
                        st.success("Admin access granted!")
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Invalid admin credentials")

    elif choice == "Submit Feedback":
        if not st.session_state.get('logged_in'):
            st.warning("Please login first")
            return
            
        st.title("💬 Submit Feedback")
        with st.form("feedback_form"):
            st.subheader("Hostel Facilities")
            hostel_feedback = st.text_area("Comments about hostel")
            hostel_rating = st.selectbox("Overall Rating", ["A", "B", "C", "D", "E"])
            
            st.subheader("Mess Feedback")
            mess_type = st.radio("Food Type", ["Veg", "Non-Veg", "Special", "Food Park"])  # Updated food options
            mess_feedback = st.text_area("Comments about food")
            mess_rating = st.selectbox("Food Rating", ["A", "B", "C", "D", "E"])
            
            st.subheader("Bathroom Feedback")
            bathroom_rating = st.selectbox("Cleanliness Rating", ["A", "B", "C", "D", "E"])
            
            other_comments = st.text_area("Other suggestions")
            
            if st.form_submit_button("Submit Feedback"):
                new_feedback = pd.DataFrame({
                    'username': [st.session_state.current_user],
                    'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    'hostel_feedback': [hostel_feedback],
                    'hostel_rating': [hostel_rating],
                    'mess_feedback': [mess_feedback],
                    'mess_type': [mess_type],
                    'mess_rating': [mess_rating],
                    'bathroom_feedback': ["N/A"],
                    'bathroom_rating': [bathroom_rating],
                    'other_comments': [other_comments]
                })
                st.session_state.feedback_db = pd.concat(
                    [st.session_state.feedback_db, new_feedback], 
                    ignore_index=True
                )
                st.success("Thank you for your feedback!")
                st.balloons()

    elif choice == "View Feedback":
        if not st.session_state.get('is_admin'):
            st.error("Admin access required")
            return
            
        st.title("📊 All Feedback Records")
        st.dataframe(st.session_state.feedback_db)
        
        if st.button("Download Feedback as CSV"):
            st.download_button(
                label="Download",
                data=st.session_state.feedback_db.to_csv().encode('utf-8'),
                file_name="hostel_feedback.csv",
                mime="text/csv"
            )

    elif choice == "User Management":
        if not st.session_state.get('is_admin'):
            st.error("Admin access required")
            return
            
        st.title("👥 User Management")
        st.dataframe(st.session_state.users_db.drop(columns=['password']))
        
        del_user = st.selectbox("Select user to remove", 
                              st.session_state.users_db['username'])
        if st.button("Delete User", type="primary"):
            st.session_state.users_db = st.session_state.users_db[
                st.session_state.users_db['username'] != del_user
            ]
            st.success(f"User {del_user} deleted")
            time.sleep(1)
            st.rerun()

    elif choice == "Logout":
        st.session_state.clear()
        st.success("Logged out successfully")
        time.sleep(1)
        st.rerun()

    elif choice == "FAQ":
        st.title("❓ Frequently Asked Questions")
        with st.expander("How to submit feedback?"):
            st.write("Login and select 'Submit Feedback'")
        with st.expander("Food categories"):
            st.write("""
            - Veg: Pure vegetarian meals
            - Non-Veg: Includes eggs, chicken, fish
            - Special: Diet-specific meals
            - Food Park: Variety food court style
            """)

if __name__ == "__main__":
    main()
