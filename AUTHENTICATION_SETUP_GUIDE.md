# 🔐 Authentication Setup Guide

Complete guide to setup Supabase authentication for the RBC Metabolic Model.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Account Setup](#supabase-account-setup)
3. [Database Configuration](#database-configuration)
4. [Local Development Setup](#local-development-setup)
5. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
6. [Creating Your First Admin](#creating-your-first-admin)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

- Python 3.11+
- Git installed
- A valid email address
- Internet connection

---

## 2. Supabase Account Setup

### Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up with GitHub, Google, or Email
4. Verify your email address

### Step 2: Create New Project

1. Click **"New Project"**
2. Fill in project details:
   - **Name:** `rbc-metabolic-model` (or your choice)
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your users (e.g., `US East` for North America)
   - **Pricing Plan:** Start with **Free tier** (500 MB database, 50k MAU)

3. Click **"Create new project"**
4. Wait 2-3 minutes for provisioning

### Step 3: Get API Credentials

1. In your project dashboard, go to **Project Settings** (gear icon)
2. Navigate to **API** section
3. Copy these values:
   - **Project URL:** `https://your-project-id.supabase.co`
   - **anon public key:** Long JWT token starting with `eyJ...`

⚠️ **Important:** Never share your `service_role` key! We only need the `anon` key.

---

## 3. Database Configuration

### Step 1: Run SQL Schema

1. In Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Open `SUPABASE_SETUP.sql` from your project root
4. Copy the entire SQL content
5. Paste into the SQL Editor
6. Click **"Run"** (or press F5)
7. Wait for success message

This creates:
- ✅ `user_profiles` table
- ✅ `simulation_history` table
- ✅ Row Level Security (RLS) policies
- ✅ Helper functions
- ✅ Indexes for performance

### Step 2: Verify Tables

Run this query to verify:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('user_profiles', 'simulation_history');
```

You should see both tables listed.

### Step 3: Enable Email Auth

1. Go to **Authentication** → **Providers**
2. Ensure **Email** provider is enabled
3. Configure email settings:
   - **Enable email confirmations:** ON (recommended)
   - **Secure email change:** ON
   - **Email templates:** Customize if desired

---

## 4. Local Development Setup

### Step 1: Install Dependencies

```bash
cd c:\Users\Jorgelindo\Desktop\Mario_RBC_up

# Activate your virtual environment
.\venv\Scripts\Activate.ps1

# Install new dependencies
pip install supabase python-dotenv
```

### Step 2: Configure Secrets

1. Create secrets file:
   ```bash
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

2. Edit `.streamlit/secrets.toml`:
   ```toml
   [supabase]
   url = "https://your-project-id.supabase.co"
   anon_key = "your-actual-anon-key-here"
   ```

3. Verify `.gitignore` includes:
   ```
   .streamlit/secrets.toml
   ```

### Step 3: Test Locally

```bash
streamlit run streamlit_app/app.py
```

Visit `http://localhost:8501` and check:
- ✅ Login page accessible at "0_Login"
- ✅ No authentication errors in console
- ✅ Can create test account

---

## 5. Streamlit Cloud Deployment

### Step 1: Push to GitHub

```bash
git add .
git commit -m "feat: add Supabase authentication system"
git push
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repository
4. Main file: `streamlit_app/app.py`
5. Python version: `3.11`

### Step 3: Configure Secrets

1. In app settings, find **"Secrets"** section
2. Paste your secrets (without comments):

```toml
[supabase]
url = "https://your-project-id.supabase.co"
anon_key = "your-actual-anon-key"
```

3. Click **"Save"**
4. Wait for app to redeploy

### Step 4: Configure Supabase Redirect URLs

1. In Supabase dashboard: **Authentication** → **URL Configuration**
2. Add these to **Redirect URLs**:
   - `http://localhost:8501`
   - `https://your-app-name.streamlit.app`

3. Save changes

---

## 6. Creating Your First Admin

### Method 1: Via Signup Page

1. Go to your app (local or deployed)
2. Click **"Sign Up"**
3. Create account with your email
4. Verify email (check inbox/spam)
5. In Supabase SQL Editor, run:

```sql
UPDATE user_profiles 
SET role = 'admin' 
WHERE email = 'your.email@example.com';
```

6. Logout and login again
7. You should now see **"Admin"** button

### Method 2: Direct SQL Insert

```sql
-- First, get your user ID from auth.users
SELECT id, email FROM auth.users;

-- Update role
UPDATE user_profiles 
SET role = 'admin' 
WHERE id = 'your-user-uuid-here';
```

---

## 7. Testing

### Test Checklist

#### Authentication Flow
- [ ] Can access login page
- [ ] Can create new account
- [ ] Receive verification email
- [ ] Can verify email
- [ ] Can login with credentials
- [ ] Invalid credentials show error
- [ ] Can logout successfully

#### Protected Pages
- [ ] Simulation page requires login
- [ ] Flux Analysis requires login
- [ ] Sensitivity Analysis requires login
- [ ] Data Upload requires login
- [ ] Redirect to login works
- [ ] After login, can access pages

#### Admin Features
- [ ] Admin can access Admin page
- [ ] Regular users cannot access Admin
- [ ] Admin can view all users
- [ ] Admin can change user roles
- [ ] Admin can deactivate users
- [ ] Analytics display correctly

#### Edge Cases
- [ ] Logout clears session
- [ ] Deactivated user cannot login
- [ ] Email validation works
- [ ] Password requirements enforced
- [ ] Duplicate email rejected

---

## 8. Troubleshooting

### Issue: "Authentication not configured"

**Solution:**
- Check `.streamlit/secrets.toml` exists
- Verify Supabase credentials are correct
- Restart Streamlit app

### Issue: "Invalid credentials" on correct password

**Solution:**
- Verify email is confirmed
- Check user exists: `SELECT * FROM auth.users WHERE email = 'your@email.com'`
- Check user profile: `SELECT * FROM user_profiles WHERE email = 'your@email.com'`

### Issue: "Failed to connect to authentication service"

**Solution:**
- Check internet connection
- Verify Supabase project is active (not paused)
- Check Supabase status: [status.supabase.com](https://status.supabase.com)

### Issue: User can't access pages after login

**Solution:**
- Clear browser cache
- Check `is_active = true` in user_profiles
- Verify RLS policies are enabled:
  ```sql
  SELECT tablename, rowsecurity FROM pg_tables 
  WHERE schemaname = 'public';
  ```

### Issue: Admin page not visible

**Solution:**
- Verify role is 'admin':
  ```sql
  SELECT email, role FROM user_profiles WHERE email = 'your@email.com';
  ```
- Logout and login again
- Check console for JavaScript errors

### Issue: Emails not sending

**Solution:**
- Check Supabase **Authentication** → **Email Templates**
- Verify email provider settings
- Check spam folder
- Consider using custom SMTP (paid plan)

### Issue: RLS blocking legitimate queries

**Solution:**
- Review RLS policies in Supabase dashboard
- Test with RLS disabled temporarily (NOT in production):
  ```sql
  ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
  ```
- Check auth token is valid

---

## 🔒 Security Best Practices

1. ✅ **Never commit** `.streamlit/secrets.toml` to git
2. ✅ **Use strong passwords** (min 12 characters)
3. ✅ **Enable email verification** in production
4. ✅ **Review RLS policies** regularly
5. ✅ **Monitor failed login attempts**
6. ✅ **Keep Supabase** libraries updated
7. ✅ **Use HTTPS only** in production
8. ✅ **Implement rate limiting** if needed

---

## 📊 Monitoring & Analytics

### View User Activity

```sql
SELECT * FROM user_activity_summary 
ORDER BY total_simulations_logged DESC;
```

### Recent Simulations

```sql
SELECT 
    up.email,
    sh.simulation_type,
    sh.created_at,
    sh.duration_seconds
FROM simulation_history sh
JOIN user_profiles up ON sh.user_id = up.id
ORDER BY sh.created_at DESC
LIMIT 50;
```

### User Growth

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM user_profiles
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## 🆘 Support

For issues specific to:
- **Supabase:** [supabase.com/docs](https://supabase.com/docs)
- **Streamlit:** [docs.streamlit.io](https://docs.streamlit.io)
- **This Project:** Open an issue on GitHub

---

## ✅ Setup Complete!

You now have a fully functional authentication system with:
- 🔐 Secure user authentication
- 👥 User management
- 🔒 Admin controls
- 📊 Usage analytics
- 🚀 Production-ready deployment

**Next Steps:**
1. Create your admin account
2. Test all features
3. Invite beta users
4. Monitor usage analytics
5. Customize email templates
6. Add custom branding

Happy simulating! 🧬
