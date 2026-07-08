--- /tmp/ui_original.py	2026-07-08 07:15:39.416683268 +0000
+++ jd-aware-resume-screener-main/frontend/ui.py	2026-07-08 07:15:18.156719259 +0000
@@ -28,7 +28,6 @@
     render_candidate_header,
     get_status_badge_html
 )
-from frontend.auth_ui import render_auth_page
 
 def build_local_hiring_insights(results, jd):
     """Build a high-quality local summary of results if AI is unavailable."""
@@ -240,14 +239,6 @@
 from config.settings import create_required_directories
 create_required_directories()
 
-# Session Authentication Guard
-if "authenticated_recruiter" not in st.session_state:
-    st.session_state["authenticated_recruiter"] = None
-
-if st.session_state["authenticated_recruiter"] is None:
-    render_auth_page()
-    st.stop()
-
 # Initialize session states
 if "current_tab" not in st.session_state:
     st.session_state["current_tab"] = "Overview"
@@ -261,122 +252,6 @@
     st.session_state["analysis_mode"] = "AI Enhanced"
 if "api_cred_source" not in st.session_state:
     st.session_state["api_cred_source"] = "Default System Key"
-if "show_profile_modal" not in st.session_state:
-    st.session_state["show_profile_modal"] = False
-if "show_password_modal" not in st.session_state:
-    st.session_state["show_password_modal"] = False
-
-# ------------------------------------------------------------------
-# Recruiter Account Dialog Modals (My Profile, Settings, Password Change)
-# ------------------------------------------------------------------
-from datetime import datetime
-
-@st.dialog("👤 Recruiter Profile & Settings")
-def show_profile_dialog():
-    rec_info = st.session_state.get("authenticated_recruiter")
-    if not rec_info:
-        st.error("No active recruiter session.")
-        return
-        
-    from database.auth import get_recruiter_details, update_recruiter_profile
-    details = get_recruiter_details(rec_info["id"])
-    if not details:
-        st.error("Could not fetch recruiter account profile.")
-        return
-        
-    st.markdown("#### Account Information")
-    st.write(f"📧 **Work Email:** `{details['email']}`")
-    st.write(f"🆔 **Recruiter ID:** `{details['id']}`")
-    
-    try:
-        created_dt = datetime.fromisoformat(details["created_date"]).strftime("%B %d, %Y %I:%M %p")
-    except Exception:
-        created_dt = details["created_date"]
-        
-    try:
-        last_login_dt = datetime.fromisoformat(details["last_login"]).strftime("%B %d, %Y %I:%M %p")
-    except Exception:
-        last_login_dt = details["last_login"]
-        
-    st.write(f"📅 **Created At:** {created_dt}")
-    st.write(f"🕒 **Last Login:** {last_login_dt}")
-    st.divider()
-    
-    st.markdown("#### Edit Profile Settings")
-    with st.form("edit_profile_form", clear_on_submit=False):
-        new_name = st.text_input("Full Name", value=details["fullname"])
-        new_company = st.text_input("Company Name", value=details["company_name"])
-        save_btn = st.form_submit_button("Save Changes", use_container_width=True)
-        
-        if save_btn:
-            if not new_name.strip() or not new_company.strip():
-                st.error("Fields cannot be empty.")
-            else:
-                success = update_recruiter_profile(details["id"], new_name.strip(), new_company.strip())
-                if success:
-                    st.session_state["authenticated_recruiter"]["fullname"] = new_name.strip()
-                    st.session_state["authenticated_recruiter"]["company_name"] = new_company.strip()
-                    st.success("Profile updated successfully!")
-                    st.rerun()
-                else:
-                    st.error("Failed to update profile.")
-
-@st.dialog("🔐 Change Password")
-def show_change_password_dialog():
-    rec_info = st.session_state.get("authenticated_recruiter")
-    if not rec_info:
-        st.error("No active recruiter session.")
-        return
-        
-    from database.auth import update_password
-    from frontend.auth_ui import check_password_policy, render_password_requirements_panel
-    
-    st.markdown("#### Update Your Password")
-    st.caption("Please configure a new secure password matching the enterprise validation rules below.")
-    
-    current_pwd = st.text_input("Current Password", type="password", key="dialog_curr_pwd")
-    new_pwd = st.text_input("New Password", type="password", key="dialog_new_pwd")
-    
-    render_password_requirements_panel(new_pwd)
-    
-    confirm_pwd = st.text_input("Confirm New Password", type="password", key="dialog_conf_pwd")
-    submit_btn = st.button("Update Password", key="dialog_pwd_submit_btn", use_container_width=True)
-    
-    if submit_btn:
-        if not current_pwd or not new_pwd or not confirm_pwd:
-            st.error("Please fill in all fields.")
-        elif not check_password_policy(new_pwd):
-            st.error("New password does not satisfy validation criteria.")
-        elif new_pwd != confirm_pwd:
-            st.error("Confirm password does not match new password.")
-        else:
-            from database.auth import get_connection, verify_password
-            conn = get_connection()
-            cursor = conn.cursor()
-            cursor.execute("SELECT password_hash FROM recruiters WHERE id = ?", (rec_info["id"],))
-            row = cursor.fetchone()
-            conn.close()
-            
-            if not row or not verify_password(row["password_hash"], current_pwd):
-                st.error("Current password incorrect.")
-            else:
-                success = update_password(rec_info["email"], new_pwd)
-                if success:
-                    st.success("Password updated successfully!")
-                    st.rerun()
-                else:
-                    st.error("Failed to update password.")
-
-# Trigger popover dialogs
-if st.session_state.get("show_profile_modal"):
-    st.session_state["show_profile_modal"] = False
-    show_profile_dialog()
-    
-if st.session_state.get("show_password_modal"):
-    st.session_state["show_password_modal"] = False
-    show_change_password_dialog()
-
-
 
 # ------------------------------------------------------------------
 # Sidebar - Configuration and Uploads
@@ -663,21 +538,8 @@
 
 
 # ------------------------------------------------------------------
-# Main Area Layout (Top Bar with Clickable Account Dropdown Popover)
+# Main Area Layout (Top Bar)
 # ------------------------------------------------------------------
-# Dynamic recruiter information
-rec_info = st.session_state.get("authenticated_recruiter")
-rec_name = rec_info["fullname"] if rec_info else "Sai Vardhan"
-rec_company = rec_info["company_name"] if rec_info else "Acme Corp"
-
-import html
-escaped_rec_name = html.escape(rec_name)
-escaped_rec_company = html.escape(rec_company)
-
-rec_names_split = rec_name.split()
-rec_initials = "".join([n[0].upper() for n in rec_names_split[:2]]) if rec_names_split else "SV"
-escaped_rec_initials = html.escape(rec_initials)
-
 # Select dynamic title text based on current tab
 tab_titles = {
     "Overview": "Screening Overview",
@@ -693,150 +555,16 @@
     "Reports": "Executive pipeline summaries and exports."
 }.get(st.session_state.get("current_tab", "Overview"), "Enterprise-grade talent assessment and shortlisting.")
 
-# Inject Custom Account Menu CSS
 st.markdown(
     f"""
-    <style>
-        /* Style the popover container to align right */
-        div[data-testid="stPopover"] {{
-            display: flex;
-            justify-content: flex-end;
-            width: 100%;
-        }}
-
-        /* Style the popover button to look like a profile card */
-        div[data-testid="stPopover"] > button {{
-            background: transparent !important;
-            border: 1px solid rgba(128, 128, 128, 0.15) !important;
-            border-radius: 8px !important;
-            padding: 6px 14px !important;
-            cursor: pointer !important;
-            transition: all 0.2s ease !important;
-            display: flex !important;
-            align-items: center !important;
-            gap: 12px !important;
-            text-align: left !important;
-            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
-            width: auto !important;
-            height: 42px !important;
-            color: var(--text-color) !important;
-        }}
-
-        div[data-testid="stPopover"] > button:hover {{
-            background: rgba(128, 128, 128, 0.05) !important;
-            border-color: rgba(128, 128, 128, 0.25) !important;
-        }}
-
-        /* Inject circular initials avatar */
-        div[data-testid="stPopover"] > button::before {{
-            content: "{escaped_rec_initials}" !important;
-            width: 30px !important;
-            height: 30px !important;
-            border-radius: 50% !important;
-            background-color: rgba(37, 99, 235, 0.08) !important;
-            color: #2563eb !important;
-            border: 1px solid rgba(37, 99, 235, 0.15) !important;
-            display: flex !important;
-            align-items: center !important;
-            justify-content: center !important;
-            font-size: 0.75rem !important;
-            font-weight: 700 !important;
-            font-family: 'Inter', sans-serif !important;
-        }}
-
-        /* Style popover menu items dropdown */
-        div[data-testid="stPopoverBody"] button {{
-            background: transparent !important;
-            border: 1px solid transparent !important;
-            color: var(--text-color) !important;
-            text-align: left !important;
-            justify-content: flex-start !important;
-            padding: 8px 12px !important;
-            font-size: 0.82rem !important;
-            font-weight: 500 !important;
-            width: 100% !important;
-            border-radius: 6px !important;
-            transition: background 0.15s ease !important;
-        }}
-
-        div[data-testid="stPopoverBody"] button:hover {{
-            background: rgba(128, 128, 128, 0.06) !important;
-        }}
-
-        /* Soft red highlight for logout */
-        div[data-testid="stPopoverBody"] button[key*="logout_dropdown_btn"] {{
-            color: #ef4444 !important;
-        }}
-
-        /* Style disabled buttons to look like muted menu items */
-        div[data-testid="stPopoverBody"] button:disabled {{
-            color: #94a3b8 !important;
-            cursor: not-allowed !important;
-            opacity: 0.65 !important;
-        }}
-    </style>
+    <div style="margin-bottom: 20px;">
+        <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-color);">{current_title}</h1>
+        <p style="margin: 3px 0 0 0; font-size: 0.85rem; color: #64748b;">{current_desc}</p>
+    </div>
     """,
     unsafe_allow_html=True
 )
 
-# Render Top Bar columns
-col_title, col_profile = st.columns([2.0, 1.0])
-
-with col_title:
-    st.markdown(
-        f"""
-        <div style="margin-bottom: 20px;">
-            <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-color);">{current_title}</h1>
-            <p style="margin: 3px 0 0 0; font-size: 0.85rem; color: #64748b;">{current_desc}</p>
-        </div>
-        """,
-        unsafe_allow_html=True
-    )
-
-with col_profile:
-    # Popover acts as the clickable recruiter profile card dropdown
-    with st.popover(
-        label=f"{escaped_rec_name} | {escaped_rec_company}",
-        use_container_width=True,
-    ):
-        st.markdown(
-            f"""
-            <div style="padding: 4px 8px; margin-bottom: 8px;">
-                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
-                    <div class="avatar-initials" style="width: 40px; height: 40px; border: 1px solid rgba(128,128,128,0.15); display: flex; align-items: center; justify-content: center; font-size: 0.95rem; font-weight: 700; background-color: rgba(37,99,235,0.08); color: #2563eb; border-radius: 50%;">
-                        {escaped_rec_initials}
-                    </div>
-                    <div>
-                        <p style="margin: 0; font-size: 0.9rem; font-weight: 700; color: var(--text-color); line-height: 1.2;">{escaped_rec_name}</p>
-                        <p style="margin: 2px 0 0 0; font-size: 0.72rem; color: #64748b; font-weight: 500;">Recruiter</p>
-                    </div>
-                </div>
-                <p style="margin: 0; font-size: 0.72rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">{escaped_rec_company}</p>
-            </div>
-            <hr style="margin: 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>
-            """,
-            unsafe_allow_html=True
-        )
-        
-        # Dropdown Actions
-        if st.button("👤 My Profile", key="profile_menu_item", use_container_width=True):
-            st.session_state["show_profile_modal"] = True
-            st.rerun()
-            
-        if st.button("⚙ Account Settings", key="settings_menu_item", use_container_width=True):
-            st.session_state["show_profile_modal"] = True
-            st.rerun()
-            
-        if st.button("🔐 Change Password", key="password_menu_item", use_container_width=True):
-            st.session_state["show_password_modal"] = True
-            st.rerun()
-        
-        st.markdown('<hr style="margin: 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>', unsafe_allow_html=True)
-        
-        if st.button("🚪 Logout", key="logout_dropdown_btn", use_container_width=True):
-            st.session_state["authenticated_recruiter"] = None
-            st.rerun()
-
 # Add a divider below top bar block
 st.markdown('<hr style="margin-top: -10px; margin-bottom: 20px; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>', unsafe_allow_html=True)