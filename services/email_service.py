import os
import smtplib
import logging
from config.settings import get_env
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logger
logger = logging.getLogger("HireSense.EmailService")

class EmailService:
    @staticmethod
    def send_password_reset_email(to_email: str, token: str) -> bool:
        """
        Send a password recovery email.
        If SMTP credentials are provided in the environment (.env), it dispatches a real email.
        Otherwise, it falls back to stdout simulation for development.
        """
        smtp_username = get_env("SMTP_USERNAME")
        smtp_password = get_env("SMTP_PASSWORD")
        smtp_server = get_env("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(get_env("SMTP_PORT", "465"))
        
        # Determine the base URL dynamically or locally
        app_url = get_env("APP_URL", "http://localhost:8501")
        reset_link = f"{app_url}/?token={token}"
        
        if smtp_username and smtp_password:
            try:
                # Set up MIME message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = to_email
                msg['Subject'] = "HireSense AI - Password Reset Request"
                
                body = f"""Hello,

We received a request to reset your password for your HireSense AI account.
Click the link below to set a new secure password. This link will expire in 15 minutes:

{reset_link}

If you did not request this reset, please ignore this email.

Best regards,
Talent Acquisition Team
HireSense AI
"""
                msg.attach(MIMEText(body, 'plain'))
                
                # Connect to SMTP server
                if smtp_port == 465:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_username, to_email, msg.as_string())
                server.quit()
                
                logger.info(f"Password reset email sent to Gmail recipient: {to_email}")
                print(f"[EMAIL_SERVICE] Real email successfully sent via SMTP to: {to_email}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send real SMTP email: {str(e)}")
                print(f"[EMAIL_SERVICE] Real SMTP delivery failed: {str(e)}. Falling back to console simulation.")
                # Fall back to simulation if real sending fails so developers aren't locked out
        
        # Fallback console simulator if no credentials configured or real SMTP failed
        try:
            logger.info(f"Password reset email simulated to recipient: {to_email}")
            print("\n" + "="*80)
            print("✉️  [OUTGOING EMAIL SIMULATOR - SMTP NOT CONFIGURED]")
            print(f"To:      {to_email}")
            print("Subject: HireSense AI - Password Reset Request")
            print("Body:")
            print("   Hello,")
            print("   We received a request to reset your password for your HireSense AI account.")
            print("   Copy and paste one of the links below into your browser (matching your current port/address).")
            print("   This link will expire in 15 minutes:")
            print("\n   👉 http://127.0.0.1:8501/?token=" + token)
            print("   👉 http://localhost:8501/?token=" + token)
            print("\n   Or manually append this parameter to your active tab's URL:")
            print("   ?token=" + token)
            print("\n   [PRO-TIP] To configure real email dispatch, add SMTP_USERNAME and SMTP_PASSWORD to your .env file.")
            print("="*80 + "\n")
            
            return True
        except Exception as e:
            logger.error(f"Failed to run simulation fallback: {str(e)}")
            return False

    @staticmethod
    def send_otp_email(to_email: str, otp: str) -> bool:
        """Send a recruiter registration verification code (OTP) via SMTP/Simulator."""
        smtp_username = get_env("SMTP_USERNAME")
        smtp_password = get_env("SMTP_PASSWORD")
        smtp_server = get_env("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(get_env("SMTP_PORT", "465"))
        
        subject = "HireSense AI - Recruiter Verification Code"
        body = f"""Hello,

Thank you for registering a recruiter account with HireSense AI.
Please verify your email address by entering the following 6-digit one-time passcode (OTP):

👉 {otp}

This code will expire in 5 minutes. If you did not request this, please ignore this email.

Best regards,
Talent Acquisition Team
HireSense AI
"""
        
        if smtp_username and smtp_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                if smtp_port == 465:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_username, to_email, msg.as_string())
                server.quit()
                
                logger.info(f"Verification OTP email sent via SMTP to: {to_email}")
                print(f"[EMAIL_SERVICE] OTP successfully sent via SMTP to: {to_email}")
                return True
            except Exception as e:
                logger.error(f"Failed to send SMTP OTP: {str(e)}")
                print(f"[EMAIL_SERVICE] Real SMTP OTP dispatch failed: {str(e)}. Falling back to simulation.")
                
        # Fallback simulator
        try:
            logger.info(f"Verification OTP email simulated to recipient: {to_email}")
            print("\n" + "="*80)
            print("✉️  [OUTGOING EMAIL SIMULATOR - OTP CODE]")
            print(f"To:      {to_email}")
            print(f"Subject: {subject}")
            print("Body:")
            print("   Hello,")
            print("   Please verify your email address by entering the following verification code:")
            print(f"\n   👉 {otp}")
            print("\n   This code will expire in 5 minutes.")
            print("="*80 + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed simulated OTP dispatch: {str(e)}")
            return False
