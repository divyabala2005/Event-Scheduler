from app import app, db, Event, Resource, Allocation

with app.app_context():
    try:
        num_alloc = db.session.query(Allocation).delete()
        num_event = db.session.query(Event).delete()
        num_res = db.session.query(Resource).delete()
        db.session.commit()
        print(f"Cleared {num_alloc} allocations, {num_event} events, {num_res} resources.")
        
        # Verify
        remaining_events = Event.query.count()
        remaining_resources = Resource.query.count()
        print(f"Remaining: Events={remaining_events}, Resources={remaining_resources}")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
