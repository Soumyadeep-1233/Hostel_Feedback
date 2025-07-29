import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import json
import requests
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText

# Page configuration
st.set_page_config(
    page_title="Hostel Feedback System",
    page_icon="🏠",
    layout="wide"
)

# Security functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_reset_token():
    return secrets.token_urlsafe(16)

# Load Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_feedback = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_szdrhwiq.json")
lottie_login = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_ktwnwv5m.json")

# Email configuration (replace with your SMTP details)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"  # Use app-specific password

def send_reset_email(to_email, reset_token):
    reset_link = f"http://yourstreamlitapp.com?reset_token={reset_token}"
    message = f"""
    You requested a password reset for Hostel Feedback System.
    Click this link to reset your password: {reset_link}
    
    If you didn't request this, please ignore this email.
    """
    
    msg = MIMEText(message)
    msg['Subject'] = "Password Reset Request"
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Initialize databases
def init_database():
    if 'users_db' not in st.session_state:
        st.session_state.users_db = pd.DataFrame(columns=['username', 'password', 'name', 'email', 'reg_no', 'room_no', 'reset_token'])
    
    if 'feedback_db' not in st.session_state:
        st.session_state.feedback_db = pd.DataFrame(columns=[
            'username', 'timestamp', 'hostel_feedback', 'hostel_rating',
            'mess_feedback', 'mess_type', 'mess_rating',
            'bathroom_feedback', 'bathroom_rating', 'other_comments'
        ])

# Authentication functions
def register_user(username, password, name, email, reg_no, room_no):
    if username in st.session_state.users_db['username'].values:
        return False, "Username already exists"
    
    hashed_pw = hash_password(password)
    new_user = pd.DataFrame({
        'username': [username],
        'password': [hashed_pw],
        'name': [name],
        'email': [email],
        'reg_no': [reg_no],
        'room_no': [room_no],
        'reset_token': [None]
    })
    
    st.session_state.users_db = pd.concat([st.session_state.users_db, new_user], ignore_index=True)
    return True, "Registration successful"

def authenticate_user(username, password):
    hashed_pw = hash_password(password)
    user = st.session_state.users_db[
        (st.session_state.users_db['username'] == username) & 
        (st.session_state.users_db['password'] == hashed_pw)
    ]
    
    if len(user) == 1:
        return True, "Login successful"
    return False, "Invalid username or password"

def initiate_password_reset(email):
    user = st.session_state.users_db[st.session_state.users_db['email'] == email]
    if len(user) == 1:
        reset_token = generate_reset_token()
        st.session_state.users_db.loc[st.session_state.users_db['email'] == email, 'reset_token'] = reset_token
        
        if send_reset_email(email, reset_token):
            return True, "Password reset link sent to your email"
    
    # Return generic message regardless to prevent email enumeration
    return True, "If your email exists, you'll receive a reset link"

def reset_password(token, new_password):
    user = st.session_state.users_db[st.session_state.users_db['reset_token'] == token]
    if len(user) == 1:
        hashed_pw = hash_password(new_password)
        username = user.iloc[0]['username']
        st.session_state.users_db.loc[st.session_state.users_db['username'] == username, 'password'] = hashed_pw
        st.session_state.users_db.loc[st.session_state.users_db['username'] == username, 'reset_token'] = None
        return True, "Password reset successful"
    return False, "Invalid or expired reset token"

# Feedback submission function remains the same as before...

def main():
    init_database()
    
    # Handle password reset from URL token
    query_params = st.experimental_get_query_params()
    reset_token = query_params.get("reset_token", [None])[0]
    
    if reset_token:
        with st.form("reset_password_form"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Reset Password"):
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                else:
                    success, message = reset_password(reset_token, new_password)
                    if success:
                        st.success(message)
                        st.experimental_set_query_params()
                        time.sleep(2)
                        st.experimental_rerun()
                    else:
                        st.error(message)
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    pages = ["Home", "Register", "Login", "Forgot Password", "FAQ", "Feedback", "View Feedback"]
    page = st.sidebar.radio("Go to", pages)
    
    # Home page (unchanged)...
    
    # Registration page (updated with email)
    elif page == "Register":
        st.title("User Registration")
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            reg_no = st.text_input("Registration Number")
            room_no = st.text_input("Room Number")
            
            if st.form_submit_button("Register"):
                success, message = register_user(username, password, name, email, reg_no, room_no)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
    
    # Login page (unchanged)...
    
    # New Forgot Password page
    elif page == "Forgot Password":
        st.title("Password Recovery")
        with st.form("forgot_password_form"):
            email = st.text_input("Registered Email Address")
            
            if st.form_submit_button("Send Reset Link"):
                success, message = initiate_password_reset(email.strip())
                st.info(message)
                if success:
                    st.write("Check your email for the password reset link.")
    
# Feedback submission
def submit_feedback(username, hostel_feedback, hostel_rating, mess_feedback, mess_type, 
                   mess_rating, bathroom_feedback, bathroom_rating, other_comments):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_feedback = pd.DataFrame({
        'username': [username],
        'timestamp': [timestamp],
        'hostel_feedback': [hostel_feedback],
        'hostel_rating': [hostel_rating],
        'mess_feedback': [mess_feedback],
        'mess_type': [mess_type],
        'mess_rating': [mess_rating],
        'bathroom_feedback': [bathroom_feedback],
        'bathroom_rating': [bathroom_rating],
        'other_comments': [other_comments]
    })
    
    st.session_state.feedback_db = pd.concat([st.session_state.feedback_db, new_feedback], ignore_index=True)
    return True, "Feedback submitted successfully"

# Main application
def main():
    init_database()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Register", "Login", "FAQ", "Feedback", "View Feedback"])
    
    # Home page
    if page == "Home":
        st.title("Hostel Feedback System 🏠")
        st.subheader("Welcome to our Hostel Feedback System")
        st.write("""
            This system allows residents to provide feedback about various aspects of hostel life, including:
            - Hostel facilities
            - Mess food quality (veg, non-veg, special, food park)
            - Bathroom cleanliness
            - General comments
            
            Please login or register to submit your feedback.
        """)
        
        if lottie_feedback:
            st_lottie(lottie_feedback, height=300, key="feedback-anim")
    
    # Registration page
    elif page == "Register":
        st.title("User Registration")
        
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            name = st.text_input("Full Name")
            reg_no = st.text_input("Registration Number")
            room_no = st.text_input("Room Number")
            
            if st.form_submit_button("Register"):
                success, message = register_user(username, password, name, reg_no, room_no)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
    
    # Login page
    elif page == "Login":
        st.title("User Login")
        
        if lottie_login:
            st_lottie(lottie_login, height=200, key="login-anim")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                success, message = authenticate_user(username, password)
                if success:
                    st.session_state.current_user = username
                    st.success(message)
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error(message)
    
    # FAQ page
    elif page == "FAQ":
        st.title("Frequently Asked Questions")
        
        with st.expander("How do I submit feedback?"):
            st.write("Navigate to the Feedback page, fill out the form, and click submit.")
        
        with st.expander("What rating system is used?"):
            st.write("We use A-E grading system where A is best and E is worst.")
        
        with st.expander("Can I see other students' feedback?"):
            st.write("Yes, you can view all feedback in the 'View Feedback' section.")
        
        with st.expander("How are mess types categorized?"):
            st.write("""
                - Vegetarian (veg)
                - Non-vegetarian (non-veg)
                - Special diet (special)
                - Food park variety (food park)
            """)
    
    # Feedback page (protected)
    elif page == "Feedback":
        st.title("Submit Feedback")
        
        if 'current_user' not in st.session_state:
            st.warning("Please login to submit feedback")
            return
        
        with st.form("feedback_form"):
            st.subheader("Hostel Feedback")
            hostel_feedback = st.text_area("Hostel Comments")
            hostel_rating = st.selectbox("Hostel Rating", ["A", "B", "C", "D", "E"])
            
            st.subheader("Mess Feedback")
            mess_type = st.radio("Mess Type", ["Veg", "Non-Veg", "Special", "Food Park"])
            mess_feedback = st.text_area("Mess Comments")
            mess_rating = st.selectbox("Mess Rating", ["A", "B", "C", "D", "E"])
            
            st.subheader("Bathroom Feedback")
            bathroom_feedback = st.text_area("Bathroom Comments")
            bathroom_rating = st.selectbox("Bathroom Rating", ["A", "B", "C", "D", "E"])
            
            st.subheader("Other Comments")
            other_comments = st.text_area("Any other comments or suggestions")
            
            if st.form_submit_button("Submit Feedback"):
                success, message = submit_feedback(
                    st.session_state.current_user,
                    hostel_feedback, hostel_rating,
                    mess_feedback, mess_type, mess_rating,
                    bathroom_feedback, bathroom_rating,
                    other_comments
                )
                
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
    
    # View Feedback page
    elif page == "View Feedback":
        st.title("View Feedback")
        
        # Show overall ratings
        st.subheader("Overall Ratings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Hostel Rating", 
                     st.session_state.feedback_db['hostel_rating'].value_counts().idxmax()
                     if not st.session_state.feedback_db.empty else "N/A")
        
        with col2:
            st.metric("Average Mess Rating", 
                     st.session_state.feedback_db['mess_rating'].value_counts().idxmax()
                     if not st.session_state.feedback_db.empty else "N/A")
        
        with col3:
            st.metric("Average Bathroom Rating", 
                     st.session_state.feedback_db['bathroom_rating'].value_counts().idxmax()
                     if not st.session_state.feedback_db.empty else "N/A")
        
        # Show feedback table
        st.subheader("All Feedback")
        
        if st.session_state.feedback_db.empty:
            st.info("No feedback submitted yet")
        else:
            st.dataframe(st.session_state.feedback_db)

if __name__ == "__main__":
    main()
