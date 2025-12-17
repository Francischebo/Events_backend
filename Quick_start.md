# Quick Start Guide

## Complete File Structure

Create the following directory structure:

```
event-management-backend/
│
├── app.py
├── config.py
├── extensions.py
├── routes.py
├── websocket_handlers.py
├── requirements.txt
├── .env.example
├── .env
├── README.md
│
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── events.py
│   ├── users.py
│   └── feed.py
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── event.py
│
└── utils/
    ├── __init__.py
    ├── decorators.py
    ├── validators.py
    ├── geolocation.py
    ├── file_upload.py
    └── email_service.py
```

## Step-by-Step Setup

### 1. Create Project Directory
```bash
mkdir event-management-backend
cd event-management-backend
```

### 2. Create Subdirectories
```bash
mkdir api models utils
```

### 3. Create __init__.py Files
```bash
touch api/__init__.py models/__init__.py utils/__init__.py
```

### 4. Install Python and MongoDB

**Python:**
- Download Python 3.8+ from python.org
- Verify: `python --version`

**MongoDB:**
- Download from mongodb.com
- Start MongoDB: `mongod`

### 5. Create Virtual Environment
```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 6. Copy All Files
Copy each file from the artifacts to the appropriate location in your project structure.

### 7. Install Dependencies
```bash
pip install -r requirements.txt
```

### 8. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

Minimum .env configuration for development:
```env
SECRET_KEY=dev-secret-key-12345
JWT_SECRET_KEY=jwt-secret-key-12345
MONGO_URI=mongodb://localhost:27017/event_management
UPLOAD_FOLDER=./uploads
```

### 9. Start the Server
```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

## Testing the API

### 1. Register a User (Attendee)
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

Expected Response:
```json
{
  "access_token": "eyJhbGc...",
  "username": "testuser",
  "role": "attendee"
}
```

### 2. Register an Organizer
To create an organizer account, you'll need to manually update the database:

```javascript
// Connect to MongoDB
mongo

// Switch to database
use event_management

// Update user role
db.users.updateOne(
  {email: "test@example.com"},
  {$set: {role: "organizer"}}
)
```

### 3. Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 4. Create an Event (Organizer Only)
```bash
curl -X POST http://localhost:5000/api/v1/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Tech Meetup",
    "description": "A gathering for tech enthusiasts",
    "date": "2025-12-25T18:00:00Z",
    "location_address": "123 Tech Street, San Francisco",
    "location": {
      "type": "Point",
      "coordinates": [-122.4194, 37.7749]
    },
    "category": "Technology",
    "geofence_radius": 200
  }'
```

### 5. Get All Events
```bash
curl http://localhost:5000/api/v1/events
```

### 6. Get Nearby Events
```bash
curl "http://localhost:5000/api/v1/events?latitude=37.7749&longitude=-122.4194&radius_km=10"
```

### 7. RSVP to Event
```bash
curl -X POST http://localhost:5000/api/v1/events/EVENT_ID/rsvp \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

## WebSocket Testing

You can test WebSocket chat using a tool like `websocat` or a JavaScript client:

```javascript
const socket = io('http://localhost:5000');

// Join chat
socket.emit('join_chat', {
  token: 'YOUR_JWT_TOKEN',
  event_id: 'EVENT_ID'
});

// Send message
socket.emit('send_message', {
  token: 'YOUR_JWT_TOKEN',
  event_id: 'EVENT_ID',
  text: 'Hello everyone!'
});

// Listen for messages
socket.on('new_message', (data) => {
  console.log(`${data.username}: ${data.text}`);
});
```

## Common Issues and Solutions

### Issue: MongoDB Connection Failed
**Solution:**
- Ensure MongoDB is running: `mongod`
- Check MONGO_URI in .env
- Try: `mongodb://127.0.0.1:27017/event_management`

### Issue: Module Not Found
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Port Already in Use
**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or change port in app.py
```

### Issue: JWT Token Expired
**Solution:**
- Login again to get a new token
- Or increase JWT_ACCESS_TOKEN_EXPIRES in config.py

### Issue: File Upload Failed
**Solution:**
- Check UPLOAD_FOLDER exists
- For cloud storage, verify AWS credentials
- Check file permissions

## Next Steps

1. **Set up email service** - Configure SMTP for password reset emails
2. **Configure cloud storage** - Set up AWS S3 for photo uploads
3. **Add more test data** - Create sample events and users
4. **Test all endpoints** - Use Postman or similar tool
5. **Set up logging** - Implement proper logging for debugging
6. **Add rate limiting** - Protect against abuse
7. **Deploy to production** - Use Docker, Heroku, or AWS

## Production Checklist

- [ ] Change all secret keys in .env
- [ ] Set DEBUG=False
- [ ] Enable HTTPS
- [ ] Set up proper logging
- [ ] Configure CORS for your frontend domain
- [ ] Set up database backups
- [ ] Implement rate limiting
- [ ] Add monitoring (e.g., Sentry)
- [ ] Use production-grade WSGI server (Gunicorn)
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure firewall rules
- [ ] Set up SSL certificates

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all dependencies are installed
3. Ensure MongoDB is running
4. Check environment variables
5. Review the README.md for detailed documentation