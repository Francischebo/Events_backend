# Complete API Testing Guide

## Authentication Endpoints

### 1. Register New User
```bash
POST http://localhost:5000/api/v1/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Expected Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "john_doe",
  "role": "attendee"
}
```

### 2. Login
```bash
POST http://localhost:5000/api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "john_doe",
  "role": "attendee"
}
```

### 3. Forgot Password
```bash
POST http://localhost:5000/api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "john@example.com"
}
```

**Expected Response (200):**
```json
{
  "message": "Password reset link sent to your email."
}
```

### 4. Logout
```bash
GET http://localhost:5000/api/v1/auth/logout
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Expected Response (200):**
```json
{
  "message": "Logged out successfully."
}
```

## Event Endpoints

### 5. Get All Events
```bash
GET http://localhost:5000/api/v1/events
```

**With filters:**
```bash
GET http://localhost:5000/api/v1/events?search=tech&latitude=37.7749&longitude=-122.4194&radius_km=10
```

**Expected Response (200):**
```json
{
  "events": [
    {
      "event_id": "507f1f77bcf86cd799439011",
      "title": "Tech Conference 2025",
      "description": "Annual tech conference",
      "date": "2025-12-15T10:00:00+00:00",
      "category": "Technology",
      "location_address": "123 Tech Street",
      "location": {
        "type": "Point",
        "coordinates": [-122.4194, 37.7749]
      },
      "organizer_id": "507f1f77bcf86cd799439012",
      "distance_km": 2.5,
      "geofence_radius": 200
    }
  ]
}
```

### 6. Create Event (Organizer Only)
```bash
POST http://localhost:5000/api/v1/events
Authorization: Bearer YOUR_ORGANIZER_TOKEN
Content-Type: application/json

{
  "title": "Flutter Workshop",
  "description": "Learn Flutter from scratch",
  "date": "2025-12-20T14:00:00Z",
  "location_address": "456 Developer Ave, San Francisco",
  "location": {
    "type": "Point",
    "coordinates": [-122.4194, 37.7749]
  },
  "category": "Education",
  "geofence_radius": 150
}
```

**Expected Response (201):**
```json
{
  "message": "Event created successfully",
  "event_id": "507f1f77bcf86cd799439013"
}
```

### 7. Update Event (Organizer Only)
```bash
PUT http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013
Authorization: Bearer YOUR_ORGANIZER_TOKEN
Content-Type: application/json

{
  "title": "Advanced Flutter Workshop",
  "description": "Advanced Flutter techniques and best practices"
}
```

**Expected Response (200):**
```json
{
  "message": "Event updated successfully"
}
```

### 8. Delete Event (Organizer Only)
```bash
DELETE http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013
Authorization: Bearer YOUR_ORGANIZER_TOKEN
```

**Expected Response (200):**
```json
{
  "message": "Event deleted successfully"
}
```

### 9. RSVP to Event
```bash
POST http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013/rsvp
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Expected Response (201):**
```json
{
  "message": "RSVP successful"
}
```

### 10. Record Arrival
```bash
POST http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013/arrival
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "message": "Arrival recorded"
}
```

### 11. Get Event Statistics (Organizer Only)
```bash
GET http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013/stats
Authorization: Bearer YOUR_ORGANIZER_TOKEN
```

**Expected Response (200):**
```json
{
  "rsvp_count": 25,
  "arrival_count": 18
}
```

### 12. Get Event Photos
```bash
GET http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013/photos
```

**Expected Response (200):**
```json
{
  "photos": [
    "https://your-bucket.s3.amazonaws.com/event123/photo1.jpg",
    "https://your-bucket.s3.amazonaws.com/event123/photo2.jpg"
  ]
}
```

### 13. Upload Event Photo
```bash
POST http://localhost:5000/api/v1/events/507f1f77bcf86cd799439013/photos
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

photo: [binary file data]
```

**Expected Response (201):**
```json
{
  "message": "Photo uploaded successfully",
  "photo_url": "https://your-bucket.s3.amazonaws.com/event123/photo3.jpg"
}
```

## User & Social Endpoints

### 14. Follow User
```bash
POST http://localhost:5000/api/v1/users/507f1f77bcf86cd799439014/follow
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "message": "Follow successful"
}
```

### 15. Unfollow User
```bash
POST http://localhost:5000/api/v1/users/507f1f77bcf86cd799439014/unfollow
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "message": "Unfollow successful"
}
```

### 16. Get Activity Feed
```bash
GET http://localhost:5000/api/v1/feed?limit=20&offset=0
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Expected Response (200):**
```json
{
  "feed": [
    {
      "activity_id": "507f1f77bcf86cd799439015",
      "actor_id": "507f1f77bcf86cd799439014",
      "actor_name": "jane_smith",
      "type": "RSVP",
      "event_id": "507f1f77bcf86cd799439013",
      "event_title": "Flutter Workshop",
      "summary": "jane_smith RSVP'd to 'Flutter Workshop'",
      "timestamp": "2025-12-01T10:30:00+00:00"
    }
  ]
}
```

### 17. Get Organizer Events
```bash
GET http://localhost:5000/api/v1/organizer/events
Authorization: Bearer YOUR_ORGANIZER_TOKEN
```

**Expected Response (200):**
```json
{
  "events": [
    {
      "event_id": "507f1f77bcf86cd799439013",
      "title": "Flutter Workshop",
      "description": "Learn Flutter from scratch",
      "date": "2025-12-20T14:00:00+00:00",
      "location_address": "456 Developer Ave",
      "organizer_id": "507f1f77bcf86cd799439012"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "message": "Missing required fields"
}
```

### 401 Unauthorized
```json
{
  "message": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "message": "Organizer access required"
}
```

### 404 Not Found
```json
{
  "message": "Event not found"
}
```

### 500 Internal Server Error
```json
{
  "message": "Failed to create event: [error details]"
}
```

## Postman Collection Setup

### Environment Variables
Create a Postman environment with these variables:

```
base_url: http://localhost:5000
access_token: (will be set automatically after login)
event_id: (sample event ID for testing)
user_id: (sample user ID for testing)
```

### Pre-request Script for Login
Add this to your login request to automatically save the token:

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

var jsonData = pm.response.json();
pm.environment.set("access_token", jsonData.access_token);
```

### Authorization Header
For authenticated requests, add header:
```
Authorization: Bearer {{access_token}}
```

## Testing Workflow

### Complete Test Flow

1. **Register User**
   - Register as attendee
   - Save token

2. **Create Organizer**
   - Register another user
   - Manually update role to "organizer" in MongoDB
   - Login with organizer account

3. **Create Event**
   - Use organizer token
   - Save event_id from response

4. **Test Event Features**
   - Get all events (no auth)
   - Search events with filters
   - RSVP to event (attendee token)
   - Upload photo
   - Get photos
   - Record arrival

5. **Test Social Features**
   - Follow organizer (attendee token)
   - Get activity feed
   - Unfollow organizer

6. **Test Organizer Features**
   - Get organizer events
   - Get event statistics
   - Update event
   - Delete event

## Load Testing

### Using Apache Bench
```bash
# Test concurrent requests
ab -n 1000 -c 10 http://localhost:5000/api/v1/events
```

### Using Python Script
```python
import requests
import concurrent.futures

def test_endpoint():
    response = requests.get('http://localhost:5000/api/v1/events')
    return response.status_code

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_endpoint) for _ in range(100)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

print(f"Success rate: {results.count(200)}/100")
```

## Security Testing

### Test Invalid Token
```bash
curl -X GET http://localhost:5000/api/v1/feed \
  -H "Authorization: Bearer invalid_token"
```

Should return 401 or 422.

### Test SQL Injection (Should be prevented)
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "\" OR \"1\"=\"1"}'
```

Should return 401, not expose data.

### Test XSS (Should be sanitized)
```bash
curl -X POST http://localhost:5000/api/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "<script>alert(\"XSS\")</script>", ...}'
```

Should store but not execute scripts.

## Monitoring Endpoints

Add these for production monitoring:

```python
# Add to app.py
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

@app.route('/metrics')
def metrics():
    return {
        'uptime': get_uptime(),
        'requests': request_count,
        'errors': error_count
    }, 200
```

## Tips for Frontend Integration

1. **Store JWT Token Securely**
   - Use secure storage (not localStorage for sensitive apps)
   - Set token in Authorization header

2. **Handle Token Expiration**
   - Implement token refresh logic
   - Show login prompt when token expires

3. **WebSocket Connection**
   - Connect with JWT token in query param
   - Implement reconnection logic

4. **Error Handling**
   - Show user-friendly messages
   - Log errors for debugging

5. **Loading States**
   - Show spinners during API calls
   - Disable buttons to prevent double submissions