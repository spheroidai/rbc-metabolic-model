# 🔐 Authentication System - Quick Reference

**Status:** ✅ Fully Implemented  
**Date:** November 22, 2025  
**Technology:** Supabase PostgreSQL + Streamlit

---

## 📦 What's Included

### Core Features
- ✅ Email/password authentication
- ✅ User registration with email verification
- ✅ Role-based access control (User / Admin)
- ✅ Protected pages requiring login
- ✅ Admin dashboard for user management
- ✅ Simulation activity tracking
- ✅ User analytics and reporting

### Security
- ✅ Row Level Security (RLS) policies
- ✅ Secure password hashing (handled by Supabase)
- ✅ Session management
- ✅ CSRF protection (Streamlit default)
- ✅ Secrets management via Streamlit secrets

---

## 📁 New Files Created

### Core Module
```
streamlit_app/core/auth.py                   # Authentication manager
```

### Pages
```
streamlit_app/pages/0_Login.py               # Login/Signup page
streamlit_app/pages/6_Admin.py               # Admin dashboard
```

### Configuration & Documentation
```
SUPABASE_SETUP.sql                           # Database schema
.streamlit/secrets.toml.template             # Secrets template
AUTHENTICATION_SETUP_GUIDE.md                # Complete setup guide
AUTHENTICATION_README.md                     # This file
```

### Modified Files
```
streamlit_app/app.py                         # Added auth widget
streamlit_app/pages/1_Simulation.py          # Protected
streamlit_app/pages/2_Flux_Analysis.py       # Protected
streamlit_app/pages/3_Sensitivity_Analysis.py # Protected
streamlit_app/pages/4_Data_Upload.py         # Protected
requirements.txt                              # Added supabase deps
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install supabase python-dotenv
```

### 2. Setup Supabase
1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Run `SUPABASE_SETUP.sql` in SQL Editor
4. Get API credentials (URL + anon key)

### 3. Configure Secrets
```bash
# Copy template
cp .streamlit/secrets.toml.template .streamlit/secrets.toml

# Edit with your credentials
nano .streamlit/secrets.toml
```

### 4. Test Locally
```bash
streamlit run streamlit_app/app.py
```

### 5. Create Admin Account
1. Sign up via the app
2. Run in Supabase SQL Editor:
```sql
UPDATE user_profiles 
SET role = 'admin' 
WHERE email = 'your.email@example.com';
```

---

## 🗂️ Database Schema

### Tables

#### `user_profiles`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (refs auth.users) |
| email | TEXT | User email (unique) |
| full_name | TEXT | Full name |
| organization | TEXT | Organization name |
| role | TEXT | 'user' or 'admin' |
| is_active | BOOLEAN | Account status |
| simulation_count | INTEGER | Total simulations run |
| created_at | TIMESTAMP | Account creation date |
| last_login | TIMESTAMP | Last login timestamp |

#### `simulation_history`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | UUID | Foreign key to user |
| simulation_type | TEXT | Type of simulation |
| parameters | JSONB | Simulation parameters |
| duration_seconds | FLOAT | Execution time |
| created_at | TIMESTAMP | Simulation date |
| success | BOOLEAN | Success status |
| error_message | TEXT | Error if failed |

---

## 🔑 User Roles

### User (Default)
**Access:**
- ✅ Home page (public)
- ✅ Simulation page
- ✅ Flux Analysis page
- ✅ Sensitivity Analysis page
- ✅ Data Upload page
- ❌ Admin dashboard

### Admin
**Access:**
- ✅ All user permissions
- ✅ Admin dashboard
- ✅ View all users
- ✅ Change user roles
- ✅ Deactivate accounts
- ✅ View analytics

---

## 🎯 Page Protection

All simulation pages are now protected:

```python
# Pages check authentication at load
if not st.session_state.authenticated:
    st.warning("Please log in to access this page")
    # Show login button
    st.stop()
```

---

## 🛠️ API Reference

### AuthManager Class

```python
from core.auth import AuthManager

auth = AuthManager()

# Sign up new user
result = auth.sign_up(email, password, full_name, organization)

# Sign in
result = auth.sign_in(email, password)

# Sign out
auth.sign_out()

# Get user profile
profile = auth.get_user_profile(user_id)

# Check if admin
is_admin = auth.is_admin(user_id)

# Log simulation
auth.log_simulation(user_id, sim_type, parameters, duration)
```

### Helper Functions

```python
from core.auth import (
    init_session_state,     # Initialize auth session
    get_user_name,          # Get current user's name
    get_user_email,         # Get current user's email
    get_user_id,            # Get current user's ID
    require_auth            # Decorator for auth (not used, inline check preferred)
)
```

---

## 📊 Usage Examples

### Check if User is Logged In
```python
if st.session_state.get("authenticated", False):
    st.success(f"Welcome, {get_user_name()}!")
else:
    st.warning("Please log in")
```

### Admin-Only Section
```python
if st.session_state.get("is_admin", False):
    st.button("Admin Panel")
else:
    st.info("Admin access required")
```

### Log Simulation Activity
```python
auth = AuthManager()
auth.log_simulation(
    user_id=get_user_id(),
    sim_type="basic",
    parameters={"duration": 42, "solver": "RK45"},
    duration=15.3
)
```

---

## 🔒 Security Notes

### What's Secure
- ✅ Passwords hashed by Supabase (bcrypt)
- ✅ Row Level Security enforced
- ✅ API keys stored in secrets (not in code)
- ✅ HTTPS in production (Streamlit Cloud)
- ✅ Email verification available

### What to Remember
- 🔑 Never commit `.streamlit/secrets.toml`
- 🔑 Use strong passwords
- 🔑 Enable email verification in production
- 🔑 Review RLS policies regularly
- 🔑 Monitor for suspicious activity

---

## 🐛 Common Issues

### "Authentication not configured"
- Check `.streamlit/secrets.toml` exists
- Verify credentials are correct
- Restart app

### Can't Login
- Verify email is confirmed
- Check password is correct
- Ensure user exists in database

### Admin Page Not Visible
- Check role is 'admin' in database
- Logout and login again

### Slow Performance
- Check Supabase region (choose closest)
- Review database indexes
- Consider caching user profiles

---

## 📈 Analytics Queries

### Total Users
```sql
SELECT COUNT(*) FROM user_profiles;
```

### Active Users (Last 7 Days)
```sql
SELECT COUNT(*) FROM user_profiles 
WHERE last_login > NOW() - INTERVAL '7 days';
```

### Simulations by Type
```sql
SELECT simulation_type, COUNT(*) 
FROM simulation_history 
GROUP BY simulation_type;
```

### Top Users
```sql
SELECT email, simulation_count 
FROM user_profiles 
ORDER BY simulation_count DESC 
LIMIT 10;
```

---

## 🔄 Migration from Previous Version

If you had the app without authentication:

1. ✅ All existing pages still work
2. ✅ Now require login to access
3. ✅ No data loss
4. ✅ Home page accessible without login
5. ✅ Gradual user onboarding possible

---

## 📞 Support

**For Setup Help:**
- See `AUTHENTICATION_SETUP_GUIDE.md`

**For Supabase Issues:**
- Docs: [supabase.com/docs](https://supabase.com/docs)
- Support: [supabase.com/support](https://supabase.com/support)

**For Streamlit Issues:**
- Docs: [docs.streamlit.io](https://docs.streamlit.io)
- Forum: [discuss.streamlit.io](https://discuss.streamlit.io)

---

## 🎉 Success Checklist

- [ ] Supabase project created
- [ ] Database schema deployed
- [ ] Secrets configured
- [ ] App runs locally
- [ ] Can create account
- [ ] Can login/logout
- [ ] Pages are protected
- [ ] Admin account created
- [ ] Admin dashboard accessible
- [ ] Deployed to Streamlit Cloud
- [ ] Production secrets configured

---

## 📝 License

This authentication system is part of the RBC Metabolic Model project.

---

**Last Updated:** November 22, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
