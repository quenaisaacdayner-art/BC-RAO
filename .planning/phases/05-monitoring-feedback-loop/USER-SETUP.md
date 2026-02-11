# Phase 5 Plan 01 - User Setup Guide

This plan requires manual setup of external services for monitoring functionality.

## Services to Configure

### 1. Resend (Transactional Email)

**Purpose:** Sends shadowban alerts and monitoring notifications to users

**Setup Steps:**

1. **Create Resend Account**
   - Go to https://resend.com
   - Sign up for free account (100 emails/day on free tier)

2. **Get API Key**
   - Navigate to: Resend Dashboard → API Keys
   - Click "Create API Key"
   - Copy the API key (starts with `re_`)

3. **Configure Sender Domain (Production)**
   - Navigate to: Resend Dashboard → Domains
   - Add your domain and verify DNS records
   - **For development:** Use Resend's onboarding domain (no verification needed)

4. **Add to Environment**
   ```bash
   # Add to bc-rao-api/.env
   RESEND_API_KEY=re_YourApiKeyHere
   EMAIL_FROM=noreply@bcrao.app  # Or your verified domain
   ```

**Dashboard Config:**
- Verify sender domain or use onboarding domain for testing
- Location: Resend Dashboard → Domains

---

### 2. Reddit API (Dual-Check Monitoring)

**Purpose:** Detects shadowbanned posts via authenticated + anonymous checks

**Setup Steps:**

1. **Create Reddit App**
   - Go to https://www.reddit.com/prefs/apps
   - Scroll to "Developed Applications"
   - Click "Create App" or "Create Another App"

2. **App Configuration**
   - **Name:** BC-RAO Monitoring (or any name)
   - **Type:** Select **"script"**
   - **Description:** (Optional) Post monitoring for BC-RAO
   - **About URL:** (Leave blank or use your site)
   - **Redirect URI:** http://localhost:8000 (required but unused for script apps)
   - Click "Create app"

3. **Get Credentials**
   - After creation, you'll see:
     - **Client ID:** String under app name (looks like: `abc123XYZ`)
     - **Secret:** Click "secret" button to reveal (looks like: `def456ABC-xyz`)

4. **Add to Environment**
   ```bash
   # Add to bc-rao-api/.env
   REDDIT_CLIENT_ID=abc123XYZ
   REDDIT_CLIENT_SECRET=def456ABC-xyz
   ```

**Dashboard Config:**
- Create Reddit "script" app at https://www.reddit.com/prefs/apps
- App type MUST be "script" (not web app or installed app)
- Redirect URI is required by Reddit but not used by BC-RAO

---

## Verification

After configuring both services, verify the setup:

```bash
# Check that env vars are loaded
cd bc-rao-api
python -c "from app.config import settings; print(f'Resend: {bool(settings.RESEND_API_KEY)}'); print(f'Reddit: {bool(settings.REDDIT_CLIENT_ID)}')"

# Expected output:
# Resend: True
# Reddit: True
```

---

## Development Mode Notes

**Resend:**
- If `RESEND_API_KEY` is empty, email service logs warnings but doesn't crash
- All email sends return `{"status": "skipped", "reason": "no_api_key"}`
- Useful for local development without Resend account

**Reddit:**
- Reddit API credentials ARE required for monitoring to work
- Without credentials, `RedditDualCheckClient` will fail on initialization
- No graceful fallback for missing Reddit credentials (monitoring is core functionality)

---

## Security Notes

- **NEVER commit .env file to git** (already in .gitignore)
- Resend API keys start with `re_` - treat as secrets
- Reddit client secrets are permanent until you regenerate them
- Use different API keys for development vs production environments

---

## Rate Limits

**Resend (Free Tier):**
- 100 emails/day
- 1 email/second
- Upgrade to paid tier for higher limits

**Reddit API:**
- OAuth apps: 60 requests/minute
- BC-RAO implements 2-second delays between auth/anon checks
- Should stay well under rate limits for typical monitoring workloads

---

## Troubleshooting

**"Reddit OAuth token request failed"**
- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are correct
- Ensure app type is "script" (not web or installed)
- Check https://www.reddit.com/prefs/apps shows your app

**"Resend email send failed"**
- Verify `RESEND_API_KEY` is correct (starts with `re_`)
- Check sender domain is verified (or use onboarding domain for testing)
- Verify you haven't exceeded free tier limits (100/day)

**"Access denied" errors**
- Check that .env file is in bc-rao-api/ directory (same level as app/)
- Restart FastAPI server after updating .env
- Verify no extra spaces in env var values

---

Setup complete when both services return True in verification step above.
