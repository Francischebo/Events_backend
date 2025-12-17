# utils/email_service.py - Email Sending Service
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)

def send_password_reset_email(email, reset_token):
    """
    Send password reset email to user
    
    Args:
        email: User's email address
        reset_token: Password reset token
    """
    try:
        # Create reset URL (modify this to match your frontend URL)
        reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
        
        # Create email message
        msg = Message(
            'Password Reset Request',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        
        # Email body
        msg.body = f'''Hello,

You have requested to reset your password. Please click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
Event Management Team
'''
        
        msg.html = f'''
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>You have requested to reset your password. Please click the button below to reset your password:</p>
                <p>
                    <a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p><em>This link will expire in 1 hour.</em></p>
                <p>If you did not request a password reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        '''
        
        # Send email
        mail.send(msg)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # In production, you might want to log this error
        # For development, we'll just print it
        return False

def send_event_reminder(email, event_title, event_date):
    """
    Send event reminder email to user
    
    Args:
        email: User's email address
        event_title: Title of the event
        event_date: Date of the event
    """
    try:
        msg = Message(
            f'Reminder: {event_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        
        msg.body = f'''Hello,

This is a reminder that you have RSVP'd to the following event:

Event: {event_title}
Date: {event_date}

We look forward to seeing you there!

Best regards,
Event Management Team
'''
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Failed to send reminder: {str(e)}")
        return False