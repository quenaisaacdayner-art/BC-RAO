"""
Email service for monitoring alerts via Resend.

Handles shadowban alerts, success notifications, and adjustment suggestions.
"""

import logging
from datetime import datetime, timedelta

import resend

from app.config import settings
from app.integrations.supabase_client import get_supabase_client


logger = logging.getLogger(__name__)


# Set Resend API key
resend.api_key = settings.RESEND_API_KEY


def send_shadowban_alert(
    user_email: str,
    user_name: str,
    post_title: str,
    subreddit: str,
    post_url: str,
    dashboard_url: str
) -> dict:
    """
    Send urgent shadowban alert email via Resend.

    Args:
        user_email: Recipient email address
        user_name: User's display name
        post_title: Title of shadowbanned post
        subreddit: Subreddit name
        post_url: Full Reddit post URL
        dashboard_url: Link to monitoring dashboard

    Returns:
        Response dict from Resend API

    Raises:
        Exception: If RESEND_API_KEY is not configured (development mode)
    """
    # Development mode: skip email if API key not configured
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured - skipping shadowban alert email")
        return {"status": "skipped", "reason": "no_api_key"}

    try:
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-header {{ background: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .alert-body {{ background: #fef2f2; border: 2px solid #dc2626; border-top: none; padding: 30px; border-radius: 0 0 8px 8px; }}
        .post-details {{ background: white; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .section {{ margin: 25px 0; }}
        .action-list {{ list-style: none; padding-left: 0; }}
        .action-list li {{ margin: 12px 0; padding-left: 24px; position: relative; }}
        .action-list li:before {{ content: "→"; position: absolute; left: 0; font-weight: bold; color: #dc2626; }}
        .cta-button {{ display: inline-block; background: #dc2626; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="alert-header">
            <h1 style="margin: 0; font-size: 24px;">🚨 SHADOWBAN DETECTED</h1>
        </div>
        <div class="alert-body">
            <p>Hi {user_name},</p>

            <p><strong>Critical Alert:</strong> One of your monitored posts has been shadowbanned by Reddit.</p>

            <div class="post-details">
                <p><strong>Subreddit:</strong> r/{subreddit}</p>
                <p><strong>Post:</strong> {post_title}</p>
                <p><strong>URL:</strong> <a href="{post_url}">{post_url}</a></p>
            </div>

            <div class="section">
                <h2 style="color: #dc2626; font-size: 18px;">What This Means</h2>
                <p>Your post is <strong>invisible to other users</strong>. Only you (when logged in) can see it. This is Reddit's silent moderation mechanism.</p>
                <p>The post appears normal to you, but generates <strong>zero engagement</strong> because nobody else can see it.</p>
            </div>

            <div class="section">
                <h2 style="color: #dc2626; font-size: 18px;">Immediate Actions</h2>
                <ul class="action-list">
                    <li><strong>Pause posting in r/{subreddit} for 48 hours</strong> – Give the subreddit breathing room</li>
                    <li><strong>Review pattern violations</strong> – Check your blacklist dashboard for detected triggers</li>
                    <li><strong>Check ISC (Invisible Spam Coefficient)</strong> – High ISC = higher shadowban risk</li>
                    <li><strong>Don't delete the post</strong> – Deleting confirms to mods you're gaming the system</li>
                </ul>
            </div>

            <div style="text-align: center;">
                <a href="{dashboard_url}" class="cta-button">View Monitoring Dashboard →</a>
            </div>

            <div class="footer">
                <p><strong>Why am I getting this?</strong> You registered this post for monitoring via BC-RAO. We check post visibility every few hours using dual-check detection (authenticated + anonymous verification).</p>
                <p>This is an automated alert. Reply with questions anytime.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        params = {
            "from": settings.EMAIL_FROM,
            "to": [user_email],
            "subject": f"URGENT: Shadowban detected in r/{subreddit}",
            "html": html_body
        }

        response = resend.Emails.send(params)
        logger.info(f"Shadowban alert sent to {user_email} for post in r/{subreddit}")
        return response

    except Exception as e:
        logger.error(f"Failed to send shadowban alert: {e}")
        # Don't crash monitoring pipeline if email fails
        return {"status": "error", "error": str(e)}


def send_success_alert(
    user_email: str,
    user_name: str,
    post_title: str,
    subreddit: str
) -> dict:
    """
    Send congratulatory email for SocialSuccess audit result.

    Args:
        user_email: Recipient email address
        user_name: User's display name
        post_title: Title of successful post
        subreddit: Subreddit name

    Returns:
        Response dict from Resend API
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured - skipping success alert email")
        return {"status": "skipped", "reason": "no_api_key"}

    try:
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .success-header {{ background: #16a34a; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .success-body {{ background: #f0fdf4; border: 2px solid #16a34a; border-top: none; padding: 30px; border-radius: 0 0 8px 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-header">
            <h1 style="margin: 0; font-size: 24px;">🎉 Social Success Achieved!</h1>
        </div>
        <div class="success-body">
            <p>Hi {user_name},</p>
            <p>Great news! Your post in <strong>r/{subreddit}</strong> has achieved Social Success status.</p>
            <p><strong>Post:</strong> {post_title}</p>
            <p>This means your post survived moderation AND earned genuine engagement (10+ upvotes or 3+ comments).</p>
            <p>Keep using these patterns for future posts in this community!</p>
        </div>
    </div>
</body>
</html>
"""

        params = {
            "from": settings.EMAIL_FROM,
            "to": [user_email],
            "subject": f"🎉 Social Success in r/{subreddit}",
            "html": html_body
        }

        response = resend.Emails.send(params)
        logger.info(f"Success alert sent to {user_email} for post in r/{subreddit}")
        return response

    except Exception as e:
        logger.error(f"Failed to send success alert: {e}")
        return {"status": "error", "error": str(e)}


def send_adjustment_alert(
    user_email: str,
    user_name: str,
    post_title: str,
    subreddit: str,
    suggestion: str
) -> dict:
    """
    Send strategy pivot suggestion for Inertia/Rejection audit results.

    Args:
        user_email: Recipient email address
        user_name: User's display name
        post_title: Title of post needing adjustment
        subreddit: Subreddit name
        suggestion: Specific adjustment suggestion text

    Returns:
        Response dict from Resend API
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured - skipping adjustment alert email")
        return {"status": "skipped", "reason": "no_api_key"}

    try:
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .neutral-header {{ background: #f59e0b; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .neutral-body {{ background: #fffbeb; border: 2px solid #f59e0b; border-top: none; padding: 30px; border-radius: 0 0 8px 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="neutral-header">
            <h1 style="margin: 0; font-size: 24px;">📊 Strategy Adjustment Suggested</h1>
        </div>
        <div class="neutral-body">
            <p>Hi {user_name},</p>
            <p>Your post in <strong>r/{subreddit}</strong> completed its 7-day audit period.</p>
            <p><strong>Post:</strong> {post_title}</p>
            <p><strong>Suggestion:</strong> {suggestion}</p>
            <p>Check your blacklist dashboard for pattern insights and adjust future posts accordingly.</p>
        </div>
    </div>
</body>
</html>
"""

        params = {
            "from": settings.EMAIL_FROM,
            "to": [user_email],
            "subject": f"Strategy adjustment for r/{subreddit}",
            "html": html_body
        }

        response = resend.Emails.send(params)
        logger.info(f"Adjustment alert sent to {user_email} for post in r/{subreddit}")
        return response

    except Exception as e:
        logger.error(f"Failed to send adjustment alert: {e}")
        return {"status": "error", "error": str(e)}


def record_alert(
    user_id: str,
    shadow_id: str,
    alert_type: str,
    subject: str,
    body_preview: str
) -> None:
    """
    Record alert in email_alerts table for rate-limiting and history.

    Args:
        user_id: User UUID
        shadow_id: Shadow entry UUID
        alert_type: Alert type (emergency, success, adjustment, etc.)
        subject: Email subject line
        body_preview: First 200 chars of email body
    """
    try:
        supabase = get_supabase_client()
        supabase.table("email_alerts").insert({
            "user_id": user_id,
            "shadow_id": shadow_id,
            "alert_type": alert_type,
            "subject": subject,
            "body_preview": body_preview[:200],
            "delivered": True  # Assume delivered if no exception
        }).execute()
        logger.info(f"Alert recorded for user {user_id}, shadow_id {shadow_id}, type {alert_type}")
    except Exception as e:
        logger.error(f"Failed to record alert: {e}")
        # Don't crash - this is just logging


def can_send_shadowban_alert(user_id: str) -> bool:
    """
    Check if user can receive another shadowban alert (rate limiting).

    Rule: Maximum 1 emergency shadowban alert per 24 hours.

    Args:
        user_id: User UUID

    Returns:
        True if allowed to send, False if rate-limited
    """
    try:
        supabase = get_supabase_client()
        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Query for recent emergency alerts
        response = supabase.table("email_alerts").select("id").eq(
            "user_id", user_id
        ).eq(
            "alert_type", "emergency"
        ).gte(
            "sent_at", cutoff.isoformat()
        ).execute()

        # Allow if no recent emergency alerts
        can_send = len(response.data) == 0
        logger.info(f"Shadowban alert rate limit check for user {user_id}: {'ALLOWED' if can_send else 'BLOCKED'}")
        return can_send

    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # On error, allow sending (fail open)
        return True
