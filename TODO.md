# TODO: Implement RBAC in Sign-Up Process

## Tasks
- [x] Update mobile/lib/screens/signup_screen.dart to add role selection dropdown (Attendee/Organizer)
- [x] Verify mobile/lib/services/auth_service.dart passes selected role to backend
- [x] Refine backend permissions in event-management-backend/api/events.py (ensure attendees can't CRUD events, only RSVP/view)
- [x] Add Organizer Analytics Dashboard screen (mobile/lib/screens/analytics_dashboard.dart) - organizer_dashboard_screen.dart already exists
- [x] Update mobile/lib/screens/main_screen.dart to show role-based UI (e.g., create event button only for organizers) - already implemented
- [x] Add backend endpoint for RSVP statistics if needed (enhance /stats) - /stats endpoint exists per event
- [x] Test role selection and permission enforcement

## Notes
- Backend already supports roles; focus on frontend role selection and UI separation.
- Attendee: Read access, RSVP, search, map, local detection.
- Organizer: All attendee features + CRUD events + analytics dashboard.
