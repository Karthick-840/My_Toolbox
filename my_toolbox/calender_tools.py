import os
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

class CalendarTool:
    """Master tool for ICS manipulation and Calendar API integration."""

    def __init__(self, output_dir="calendars"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # --- 1. ICS FILE MANIPULATION ---
    
    def create_ics(self, title, start_time, duration_hours=1, description="", filename="event.ics"):
        """Creates or updates a local .ics file."""
        cal = Calendar()
        cal.add('prodid', '-//My Learning Toolbox//')
        cal.add('version', '2.0')

        event = Event()
        event.add('summary', title)
        event.add('dtstart', start_time)
        event.add('dtend', start_time + timedelta(hours=duration_hours))
        event.add('description', description)
        event.add('dtstamp', datetime.now(pytz.utc))

        cal.add_component(event)

        path = os.path.join(self.output_dir, filename)
        with open(path, 'wb') as f:
            f.write(cal.to_ical())
        
        print(f"ICS file created: {path}")
        return path

    # --- 2. API INTEGRATION LOGIC (Architectural Framework) ---

    def sync_to_google(self, event_data):
        """
        Logic for Google Calendar API.
        Requires: google-auth, google-auth-oauthlib, google-api-python-client
        """
        print("Connecting to Google Calendar API...")
        # Placeholder for discovery.build('calendar', 'v3', credentials=creds)
        # service.events().insert(calendarId='primary', body=event_data).execute()
        pass

    def sync_to_outlook(self, event_data):
        """
        Logic for Microsoft Graph API (Outlook).
        Requires: O365 or msal library
        """
        print("Connecting to Microsoft Graph (Outlook)...")
        # Placeholder for account.calendar().new_event().save()
        pass

    # --- 3. COGNITIVE INTEGRATION ---
    
    def schedule_spaced_repetition(self, material_title, start_date):
        """
        Automates ICS creation based on the Spaced Repetition method.
        Uses the 2, 7, 30 day logic discussed.
        """
        intervals = [2, 7, 30]
        for days in intervals:
            review_date = start_date + timedelta(days=days)
            self.create_ics(
                title=f"Review: {material_title}",
                start_time=review_date,
                description=f"Spaced repetition session for {material_title}",
                filename=f"{material_title.replace(' ', '_')}_day{days}.ics"
            )

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    master = CalendarTool()
    
    # Create a single event
    now = datetime.now(pytz.utc)
    master.create_ics("Design Patterns Study", now, description="Study Proxy and Composite patterns")

    # Automate a learning schedule
    master.schedule_spaced_repetition("Python Design Patterns", now)