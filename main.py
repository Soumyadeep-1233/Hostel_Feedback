import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import json
import requests

# Page configuration
st.set_page_config(
    page_title="Hostel Feedback System",
    page_icon="🏠",
    layout="wide"
)

# Load Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_feedback = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_szdrhwiq.json")
lottie_login = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_ktwnwv5m.json")

# Create sample database files if they don't exist
def init_database():
    if 'users_db' not in st.session_state:
        st.session_state.users_db = pd.DataFrame(columns=['username', 'password', 'name', 'reg_no', 'room_no'])
    
    if 'feedback_db' not in st.session_state:
        st.session_state.feedback_db = pd.DataFrame(columns=[
            'username', 'timestamp', 'hostel_feedback', 'hostel_rating',
            'mess_feedback', 'mess_type', 'mess_rating',
            'bathroom_feedback', 'bathroom_rating',
            'other_comments'
        ])

# Authentication functions
def register_user(username, password, name, reg_no, room_no):
    if username in st.session_state.users_db['username'].values:
        return False, "Username already exists"
    
    new_user = pd.DataFrame({
        'username': [username],
        'password': [password],
        'name': [name],
        'reg_no': [reg_no],
        'room_no': [room_no]
    })
    
    st.session_state.users_db = pd.concat([st.session_state.users_db, new_user], ignore_index=True)
    return True, "Registration successful"

def authenticate_user(username, password):
    user = st.session_state.users_db[
        (st.session_state.users_db['username'] == username) & 
        (st.session_state.users_db['password'] == password)
    ]
    
    if len(user) == 1:
        return True, "Login successful"
    return False, "Invalid username or password"

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
