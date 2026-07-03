"""
auth.py
Login & Registration UI screens for the Streamlit app.
"""

import streamlit as st
import database as db


def show_auth_screen():
    """Render the login/register screen. Sets st.session_state.user on success."""

    st.markdown(
        """
        <div class="auth-hero">
            <div class="auth-logo">🎓</div>
            <h1>LICT Campus Assistant</h1>
            <p>Your AI guide to Lumbini ICT Campus — courses, admissions, and more</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Create Account"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            identifier = st.text_input("Username or Email", placeholder="e.g. shuvanjan or you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("Login 🚀", use_container_width=True)
            with col2:
                guest = st.form_submit_button("Continue as Guest 👤", use_container_width=True)

            if submitted:
                if not identifier or not password:
                    st.error("Please fill in both fields.")
                else:
                    user = db.authenticate_user(identifier, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['username']}! 🎉")
                        st.rerun()
                    else:
                        st.error("Invalid username/email or password.")

            if guest:
                st.session_state.user = {
                    "id": 0,
                    "username": "guest",
                    "email": "guest@local",
                    "full_name": "Guest",
                    "theme": "dark",
                }
                st.rerun()

    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", placeholder="Shuvanjan Sharma")
            new_username = st.text_input("Choose a Username", placeholder="shuvanjan")
            new_email = st.text_input("Email", placeholder="you@example.com")
            new_password = st.text_input("Choose a Password", type="password", placeholder="At least 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            agree = st.checkbox("I agree this is for a personal learning project.")
            reg_submitted = st.form_submit_button("Create Account ✨", use_container_width=True)

            if reg_submitted:
                if not agree:
                    st.warning("Please confirm the checkbox to continue.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = db.register_user(new_username, new_email, new_password, full_name)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
