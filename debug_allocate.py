from app import app, db, Event, Resource
from forms import AllocationForm

with app.app_context():
    try:
        print("Initializing form...")
        form = AllocationForm()
        
        print("Querying events...")
        events = Event.query.all()
        print(f"Found {len(events)} events.")
        
        print("Populating event choices...")
        # Reproducing the exact line from app.py
        form.event_id.choices = [(e.id, f"{e.title} ({e.start_time.strftime('%Y-%m-%d %H:%M')})") for e in events]
        print("Event choices populated.")
        
        print("Querying resources...")
        resources = Resource.query.all()
        print(f"Found {len(resources)} resources.")
        
        print("Populating resource choices...")
        form.resource_id.choices = [(r.id, f"{r.name} ({r.type})") for r in resources]
        print("Resource choices populated.")
        
        print("Success! Logic seems fine with empty/full DB.")
    except Exception as e:
        import traceback
        traceback.print_exc()
