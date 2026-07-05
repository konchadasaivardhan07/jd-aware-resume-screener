import streamlit as st
import os
import html
import re
from database.auth import (
    register_recruiter, 
    authenticate_recruiter, 
    update_password,
    create_password_reset_token,
    verify_password_reset_token,
    execute_password_reset,
    create_email_otp,
    verify_email_otp,
    recruiter_email_exists
)
from frontend.components import inject_custom_css
from services.email_service import EmailService

def check_password_policy(password: str) -> bool:
    """Check if the password meets all the policy requirements."""
    if not (8 <= len(password) <= 16):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#\$%\^&\*\(\)_\+=\[\]\{\}\|\\:;\"'<>,\.\?/~`\-]", password):
        return False
    if " " in password:
        return False
    return True

def render_password_requirements_panel(password: str):
    """Render a clean, enterprise-style visual indicator panel for password requirements."""
    len_ok = 8 <= len(password) <= 16
    upper_ok = bool(re.search(r"[A-Z]", password))
    lower_ok = bool(re.search(r"[a-z]", password))
    digit_ok = bool(re.search(r"\d", password))
    special_ok = bool(re.search(r"[!@#\$%\^&\*\(\)_\+=\[\]\{\}\|\\:;\"'<>,\.\?/~`\-]", password))
    no_spaces_ok = " " not in password and len(password) > 0

    def get_indicator(satisfied: bool) -> str:
        color = "var(--success-accent)" if satisfied else "var(--danger-accent)"
        char = "&#10003;" if satisfied else "&#10007;"
        return f"<span style='color: {color}; font-weight: 700; margin-right: 6px;'>{char}</span>"

    html_content = f"""
    <div style="background-color: rgba(128,128,128,0.02); border: 1px solid rgba(128,128,128,0.08); border-radius: 6px; padding: 10px; margin-top: -6px; margin-bottom: 14px; font-size: 0.76rem; font-family: 'Inter', sans-serif;">
        <p style="margin: 0 0 6px 0; font-weight: 700; color: var(--text-color);">Password Requirements</p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; color: #64748b;">
            <div>{get_indicator(len_ok)} 8–16 characters</div>
            <div>{get_indicator(upper_ok)} One uppercase letter</div>
            <div>{get_indicator(lower_ok)} One lowercase letter</div>
            <div>{get_indicator(digit_ok)} One number</div>
            <div>{get_indicator(special_ok)} One special character</div>
            <div>{get_indicator(no_spaces_ok)} No spaces</div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def render_auth_page():
    inject_custom_css()
    
    # Intercept query parameter reset token
    if "token" in st.query_params:
        st.session_state["auth_view"] = "reset_token"
        
    st.markdown(
        """
        <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
            <h2 style="font-size: 2.2rem; font-weight: 800; color: #2563eb; margin: 0; letter-spacing: -0.04em;">HireSense AI</h2>
            <p style="color: #64748b; font-size: 0.95rem; margin-top: 5px;">Enterprise Talent Assessment & Screening Portal</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"
        
    view = st.session_state["auth_view"]
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.container(border=True):
            if view == "login":
                st.markdown("<h3 style='margin-top:0; font-size:1.3rem; font-weight:700;'>Recruiter Sign In</h3>", unsafe_allow_html=True)
                st.caption("Access your talent screening workspace.")
                
                with st.form("login_form", clear_on_submit=False):
                    email = st.text_input("Work Email", placeholder="recruiter@company.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    remember = st.checkbox("Remember Me", value=True)
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    
                    if submit:
                        if not email or not password:
                            st.error("Please fill in all fields.")
                        else:
                            recruiter = authenticate_recruiter(email, password)
                            if recruiter:
                                st.session_state["authenticated_recruiter"] = recruiter
                                st.success("Authentication successful!")
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")
                                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Create Account", key="go_signup", use_container_width=True):
                        st.session_state["auth_view"] = "signup"
                        st.rerun()
                with col_btn2:
                    if st.button("Forgot Password?", key="go_forgot", use_container_width=True):
                        st.session_state["auth_view"] = "forgot"
                        st.rerun()
                        
            elif view == "signup":
                st.markdown("<h3 style='margin-top:0; font-size:1.3rem; font-weight:700;'>Create Recruiter Account</h3>", unsafe_allow_html=True)
                st.caption("Join your talent acquisition team on HireSense.")
                
                fullname = st.text_input("Full Name", placeholder="Jane Doe")
                company = st.text_input("Company Name", placeholder="Acme Corp")
                email = st.text_input("Work Email", placeholder="recruiter@company.com")
                password = st.text_input("Create Password", type="password", placeholder="Min. 8 characters")
                
                # Render real-time visual checklist
                render_password_requirements_panel(password)
                
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                submit = st.button("Register & Get Started", key="signup_submit_btn", use_container_width=True)
                
                if submit:
                    if not fullname or not company or not email or not password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif not check_password_policy(password):
                        st.error("Please ensure your password meets all validation policy requirements.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif recruiter_email_exists(email):
                        st.error("An account with this email already exists.")
                    else:
                        # Generate OTP
                        otp = create_email_otp(email)
                        # Dispatch email
                        EmailService.send_otp_email(email, otp)
                        
                        # Store context in session state
                        st.session_state["signup_fullname"] = fullname
                        st.session_state["signup_company"] = company
                        st.session_state["signup_email"] = email
                        st.session_state["signup_password"] = password
                        
                        import time
                        st.session_state["otp_sent_time"] = time.time()
                        
                        st.session_state["auth_view"] = "otp_verify"
                        st.rerun()
                                
                if st.button("Already have an account? Sign In", key="back_to_login_signup", use_container_width=True):
                    st.session_state["auth_view"] = "login"
                    st.rerun()
                    
            elif view == "otp_verify":
                st.markdown("<h3 style='margin-top:0; font-size:1.3rem; font-weight:700;'>Email Verification</h3>", unsafe_allow_html=True)
                st.info("We've sent a verification code to your email.")
                
                # Check for simulated sandbox bypass code
                if "last_simulated_otp" in st.session_state:
                    otp = st.session_state["last_simulated_otp"]
                    st.markdown(
                        f"""
                        <div style="background-color: rgba(255, 165, 0, 0.08); border: 1px dashed orange; border-radius: 6px; padding: 10px; margin-top: 6px; margin-bottom: 14px;">
                            <p style="margin: 0; color: #d97706; font-size: 0.82rem; font-weight: 600;">⚠️ Sandbox Mode Bypass</p>
                            <p style="margin: 4px 0 0 0; font-size: 0.76rem; color: var(--text-color);">
                                Streamlit Cloud blocks outgoing SMTP sockets. Use this code to register: 
                                <strong style="font-size: 0.88rem; color: #2563eb; font-family: monospace;">{otp}</strong>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                signup_email = st.session_state.get("signup_email", "")
                st.caption(f"Verification code sent to: **{html.escape(signup_email)}**")
                
                otp_input = st.text_input("Enter 6-Digit Code", max_chars=6, placeholder="123456")
                
                import time
                sent_time = st.session_state.get("otp_sent_time", 0.0)
                elapsed = time.time() - sent_time
                cooldown_remaining = max(0, int(30 - elapsed))
                
                col_otp1, col_otp2 = st.columns(2)
                with col_otp1:
                    verify_clicked = st.button("Verify & Register", key="otp_verify_btn", use_container_width=True)
                with col_otp2:
                    if cooldown_remaining > 0:
                        st.button(f"Resend OTP (Wait {cooldown_remaining}s)", key="otp_resend_disabled_btn", disabled=True, use_container_width=True)
                    else:
                        resend_clicked = st.button("Resend OTP", key="otp_resend_active_btn", use_container_width=True)
                        if resend_clicked:
                            st.session_state.pop("last_simulated_otp", None)
                            new_otp = create_email_otp(signup_email)
                            EmailService.send_otp_email(signup_email, new_otp)
                            st.session_state["otp_sent_time"] = time.time()
                            st.success("A new verification code has been sent.")
                            st.rerun()
                            
                if verify_clicked:
                    if not otp_input:
                        st.error("Please enter the verification code.")
                    elif verify_email_otp(signup_email, otp_input):
                        fullname = st.session_state.get("signup_fullname")
                        company = st.session_state.get("signup_company")
                        password = st.session_state.get("signup_password")
                        
                        success = register_recruiter(fullname, signup_email, company, password)
                        if success:
                            st.success("Account created successfully.")
                            for key in ["signup_fullname", "signup_company", "signup_email", "signup_password", "otp_sent_time", "last_simulated_otp"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.session_state["auth_view"] = "login"
                            st.rerun()
                        else:
                            st.error("Failed to create account. Please contact support.")
                    else:
                        st.error("OTP expired, incorrect, or already used.")
                        
                if st.button("Back to Sign In", key="back_to_login_otp", use_container_width=True):
                    for key in ["signup_fullname", "signup_company", "signup_email", "signup_password", "otp_sent_time", "last_simulated_otp"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state["auth_view"] = "login"
                    st.rerun()
                    
            elif view == "forgot":
                st.markdown("<h3 style='margin-top:0; font-size:1.3rem; font-weight:700;'>Recover Password</h3>", unsafe_allow_html=True)
                st.caption("Enter your email address to request a one-time password recovery link.")
                
                email = st.text_input("Work Email", placeholder="recruiter@company.com")
                submit = st.button("Request Reset Link", key="forgot_submit_btn", use_container_width=True)
                
                if submit:
                    if not email:
                        st.error("Please enter your email address.")
                    else:
                        st.session_state.pop("last_simulated_reset_link", None)
                        # Generate token (sends email if email exists, dummy delay logic matches timer mitigation)
                        token = create_password_reset_token(email)
                        if token:
                            EmailService.send_password_reset_email(email, token)
                            
                        # Always show the same success message to mitigate email enumeration attacks
                        st.success("If an account exists, a password reset link has been sent.")
                        
                        # Check for simulated sandbox bypass link
                        if "last_simulated_reset_link" in st.session_state:
                            link = st.session_state["last_simulated_reset_link"]
                            st.markdown(
                                f"""
                                <div style="background-color: rgba(255, 165, 0, 0.08); border: 1px dashed orange; border-radius: 6px; padding: 10px; margin-top: 12px; margin-bottom: 12px;">
                                    <p style="margin: 0; color: #d97706; font-size: 0.82rem; font-weight: 600;">⚠️ Sandbox Mode Bypass</p>
                                    <p style="margin: 4px 0 0 0; font-size: 0.76rem; color: var(--text-color);">
                                        Streamlit Cloud blocks outgoing SMTP sockets. Use this link to reset password:
                                        <br><a href="{link}" target="_self" style="font-weight: 700; color: #2563eb; text-decoration: underline;">👉 Reset Password Link</a>
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                                
                if st.button("Back to Sign In", key="back_to_login_forgot", use_container_width=True):
                    st.session_state.pop("last_simulated_reset_link", None)
                    st.session_state["auth_view"] = "login"
                    st.rerun()

            elif view == "reset_token":
                st.markdown("<h3 style='margin-top:0; font-size:1.3rem; font-weight:700;'>Set New Password</h3>", unsafe_allow_html=True)
                
                token = st.query_params.get("token")
                token_details = verify_password_reset_token(token)
                
                if not token_details:
                    st.error("This password reset link is invalid or has expired. Please request a new recovery link.")
                    if st.button("Back to Sign In", key="reset_token_back_err_btn", use_container_width=True):
                        st.query_params.clear()
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                else:
                    st.caption(f"Resetting password for recruiter: **{html.escape(token_details['email'])}**")
                    
                    new_password = st.text_input("New Password", type="password", placeholder="Min. 8 characters")
                    render_password_requirements_panel(new_password)
                    
                    confirm_new = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                    submit = st.button("Update Password", key="reset_token_submit_btn", use_container_width=True)
                    
                    if submit:
                        if not new_password or not confirm_new:
                            st.error("Please fill in all fields.")
                        elif not check_password_policy(new_password):
                            st.error("Please ensure your password meets all validation policy requirements.")
                        elif new_password != confirm_new:
                            st.error("Passwords do not match.")
                        else:
                            success = execute_password_reset(token, new_password)
                            if success:
                                st.success("Password updated successfully! Please sign in.")
                                st.query_params.clear()
                                st.session_state["auth_view"] = "login"
                                st.rerun()
                            else:
                                st.error("Failed to reset password. The link might have expired or been reused.")
                                
                    if st.button("Back to Sign In", key="reset_token_back_btn", use_container_width=True):
                        st.query_params.clear()
                        st.session_state["auth_view"] = "login"
                        st.rerun()
