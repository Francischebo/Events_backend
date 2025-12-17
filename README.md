# Event Management Backend API

A comprehensive Flask-based backend API for an event management system with real-time chat, geolocation features, and social interactions.

## Features

- **Authentication**: JWT-based authentication with role-based access control
- **Event Management**: Create, update, delete, and discover events
- **Geolocation**: Find nearby events using MongoDB geospatial queries
- **Real-time Chat**: WebSocket-based chat for each event
- **Social Features**: Follow/unfollow users, activity feed
- **Photo Uploads**: Cloud storage integration for event photos
- **RSVP & Attendance**: Track event RSVPs and arrivals via geofencing

## Project Structure

```
backend/
├── app.py                      # Application entry point
├── config.py                   # Configuration settings
├── extensions.py               # Flask extensions initialization
├── routes.py                   # Blueprint registration
├── websocket_handlers.py       # WebSocket event handlers
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
│
├── api/                       # API endpoints
│   ├── auth.py               # Authentication routes
│   ├── events.py             # Event management routes
│   ├── users.py              # User management routes
│   └── feed.py               # Feed and organizer routes
│
├── models/                    # Data models
│   ├── user.py               # User model
│   └── event.py              # Event model
│
└── utils/                     # Utility functions
    ├── decorators.py         # Custom decorators
    ├── validators.py         # Input validation
    ├── geolocation.py        # Geolocation utilities
    ├── file_upload.py        # File upload handling
    └── email_service.py      # Email sending service
```

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.0 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the root of the `event-management-backend` directory by copying the example file:

   ```powershell
   copy .env.example .env
   ```

   Edit the `.env` file and fill in the required values. **Do not commit the `.env` file to version control.**

   Required environment variables:
   - `SECRET_KEY`: A strong random string used for session and security. Generate one with:

     ```powershell
     python -c "import os; print(os.urandom(24).hex())"
     ```

   - `MONGO_URI`: The full MongoDB connection string. For Atlas, this typically looks like:

     ```text
     mongodb+srv://<user>:<password>@cluster0.mongodb.net/<dbname>?retryWrites=true&w=majority
     ```

     Instead of committing the URI, set it as an environment variable. On Windows PowerShell you can set it for the current session with:

     ```powershell
     $env:MONGO_URI = "mongodb+srv://user:password@cluster0.mongodb.net/mydb?retryWrites=true&w=majority"
     ```

   - `MONGO_DBNAME` (optional): If your `MONGO_URI` does not include a database name, set this (default: `event_management`).

   - `JWT_SECRET_KEY`: A strong random string for signing JWTs. Generate one similarly to `SECRET_KEY` above.

   See `.env.example` for a full list of available configuration options.


5. **Start MongoDB**
   ```bash
   # Make sure MongoDB is running
   mongod
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/forgot-password` - Request password reset
- `GET /api/v1/auth/logout` - Logout user

### Events

- `GET /api/v1/events` - Get all events (with optional filters)
- `POST /api/v1/events` - Create new event (Organizer only)
- `PUT /api/v1/events/<event_id>` - Update event (Organizer only)
- `DELETE /api/v1/events/<event_id>` - Delete event (Organizer only)
- `POST /api/v1/events/<event_id>/rsvp` - RSVP to event
- `POST /api/v1/events/<event_id>/arrival` - Record arrival at event
- `GET /api/v1/events/<event_id>/stats` - Get event statistics
- `GET /api/v1/events/<event_id>/photos` - Get event photos
- `POST /api/v1/events/<event_id>/photos` - Upload event photo

### Users & Social

- `POST /api/v1/users/<user_id>/follow` - Follow user
- `POST /api/v1/users/<user_id>/unfollow` - Unfollow user
- `GET /api/v1/feed` - Get personalized activity feed

### Organizer

- `GET /api/v1/organizer/events` - Get organizer's events

### WebSocket Chat

- `ws://localhost:5000/ws/chat/<event_id>?token=<jwt_token>`

## WebSocket Events

### Client → Server

- `join_chat` - Join event chat room
- `leave_chat` - Leave event chat room
- `send_message` - Send chat message

### Server → Client

- `user_joined` - User joined chat
- `user_left` - User left chat
- `new_message` - New chat message
- `recent_messages` - Recent chat history
- `error` - Error message

## MongoDB Collections

### users
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "role": "attendee|organizer",
  "following": ["ObjectId"],
  "followers": ["ObjectId"],
  "created_events": ["ObjectId"],
  "rsvped_events": ["ObjectId"],
  "created_at": "ISODate"
}
```

### events
```json
{
  "_id": "ObjectId",
  "title": "string",
  "description": "string",
  "date": "ISODate",
  "category": "string",
  "location_address": "string",
  "location": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  },
  "organizer_id": "ObjectId",
  "rsvps": ["ObjectId"],
  "arrivals": ["ObjectId"],
  "photo_gallery": ["string"],
  "geofence_radius": "number",
  "created_at": "ISODate"
}
```

### messages
```json
{
  "_id": "ObjectId",
  "event_id": "ObjectId",
  "user_id": "ObjectId",
  "username": "string",
  "text": "string",
  "timestamp": "ISODate"
}
```

### activities
```json
{
  "_id": "ObjectId",
  "actor_id": "ObjectId",
  "actor_name": "string",
  "type": "RSVP|EVENT_CREATED|PHOTO_UPLOADED|FOLLOW",
  "event_id": "ObjectId",
  "target_user_id": "ObjectId",
  "summary": "string",
  "timestamp": "ISODate"
}
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key configurations:
- **SECRET_KEY**: Flask secret key
- **MONGO_URI**: MongoDB connection string
- **JWT_SECRET_KEY**: JWT token secret
- **CLOUD_STORAGE_BUCKET**: AWS S3 bucket for photo uploads
- **MAIL_SERVER**: SMTP server for emails

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- Input validation
- CORS protection
- Rate limiting (recommended for production)

## Development

### Running Tests

```bash
# Set testing environment
export FLASK_ENV=testing

# Run tests (create tests later)
pytest tests/
```

### Database Indexes

The application automatically creates necessary indexes on startup:
- Users: email (unique), username (unique)
- Events: location (2dsphere), organizer_id, date
- Messages: event_id + timestamp
- Activities: actor_id + timestamp, timestamp

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Recommendations

- Use environment-specific configuration
- Enable HTTPS/TLS
- Set up proper logging
- Implement rate limiting
- Use a reverse proxy (Nginx)
- Set up monitoring and alerts
- Regular database backups
- Implement token blacklisting for logout

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running
- Check MONGO_URI in .env
- Verify network connectivity

### WebSocket Connection Issues
- Check CORS settings
- Verify JWT token is valid
- Ensure eventlet is installed

### Photo Upload Issues
- Check AWS credentials
- Verify S3 bucket permissions
- Check file size limits

## API Response Examples

### Success Response
```json
{
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "message": "Error description"
}
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Contact: support@yourapp.com