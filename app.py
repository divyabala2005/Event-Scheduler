from flask import Flask, render_template, redirect, flash, request
from models import db, Event, Resource, Allocation
from forms import EventForm, ResourceForm, AllocationForm
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return redirect('/events')

@app.route('/events', methods=['GET', 'POST'])
def events():
    form = EventForm()
    if form.validate_on_submit():
        if form.start_time.data >= form.end_time.data:
            flash("Error: End time must be after start time")
            return redirect('/events')
            
        event = Event(
            title=form.title.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            description=form.description.data
        )
        db.session.add(event)
        db.session.commit()
        flash("Event added successfully")
        return redirect('/events')
    return render_template('events.html', form=form, events=Event.query.all())

@app.route('/edit_event/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    event = Event.query.get_or_404(id)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        if form.start_time.data >= form.end_time.data:
            flash("Error: End time must be after start time")
            return render_template('events.html', form=form, events=Event.query.all(), edit_mode=True)

        event.title = form.title.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.description = form.description.data
        db.session.commit()
        flash("Event updated successfully")
        return redirect('/events')
    # Render same template but could indicate edit mode if needed, or separate template. 
    # For simplicity reusing events.html structure might be tricky without modification.
    # Let's render a specific edit view or reuse events.html with flag.
    return render_template('events.html', form=form, events=Event.query.all(), edit_id=id)

@app.route('/resources', methods=['GET', 'POST'])
def resources():
    form = ResourceForm()
    if form.validate_on_submit():
        res = Resource(name=form.name.data, type=form.type.data)
        db.session.add(res)
        db.session.commit()
        flash("Resource added successfully")
        return redirect('/resources')
    return render_template('resources.html', form=form, resources=Resource.query.all())

@app.route('/edit_resource/<int:id>', methods=['GET', 'POST'])
def edit_resource(id):
    resource = Resource.query.get_or_404(id)
    form = ResourceForm(obj=resource)
    if form.validate_on_submit():
        resource.name = form.name.data
        resource.type = form.type.data
        db.session.commit()
        flash("Resource updated successfully")
        return redirect('/resources')
    return render_template('resources.html', form=form, resources=Resource.query.all(), edit_id=id)

@app.route('/allocate', methods=['GET', 'POST'])
def allocate():
    form = AllocationForm()
    # Dynamic choices
    form.event_id.choices = [(e.id, f"{e.title} ({e.start_time.strftime('%Y-%m-%d %H:%M') if e.start_time else 'No Date'})") for e in Event.query.all()]
    form.resource_id.choices = [(r.id, f"{r.name} ({r.type})") for r in Resource.query.all()]

    if form.validate_on_submit():
        event = Event.query.get(form.event_id.data)
        resource = Resource.query.get(form.resource_id.data)
        
        # Conflict Check
        allocations = Allocation.query.filter_by(resource_id=resource.id).all()
        for alloc in allocations:
            e = Event.query.get(alloc.event_id)
            if e.id != event.id: # Don't check against itself if re-allocating (though logic doesn't support re-alloc yet)
                if e.start_time < event.end_time and event.start_time < e.end_time:
                    flash("Conflict detected! Could not allocate.")
                    detected_conflict = {
                        'new_event': event,
                        'existing_event': e,
                        'resource': resource,
                        'type': 'New Allocation Conflict'
                    }
                    return render_template('conflicts.html', conflicts=[detected_conflict])

        # Save
        # Check if already allocated to specific resource?
        existing = Allocation.query.filter_by(event_id=event.id, resource_id=resource.id).first()
        if not existing:
            db.session.add(Allocation(event_id=event.id, resource_id=resource.id))
            db.session.commit()
            flash("Resource allocated successfully")
            return redirect('/allocate')
        else:
             flash("This event is already allocated to this resource.")

    return render_template('allocate.html', form=form)

@app.route('/conflicts')
def conflicts():
    conflict_list = []
    allocs = Allocation.query.all()
    for a in allocs:
        for b in allocs:
            if a.id != b.id and a.resource_id == b.resource_id:
                e1 = Event.query.get(a.event_id)
                e2 = Event.query.get(b.event_id)
                if e1.start_time < e2.end_time and e2.start_time < e1.end_time:
                    # Avoid duplicates (A vs B, B vs A) by ID check
                    if e1.id < e2.id:
                        conflict_list.append({
                            'new_event': e1,
                            'existing_event': e2,
                            'resource': Resource.query.get(a.resource_id),
                            'type': 'Existing Database Conflict'
                        })
    return render_template('conflicts.html', conflicts=conflict_list)

@app.route('/report')
def report():
    # Get date range from query params (default to last 30 days if not set, or just show all)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
            
    if end_date_str:
         try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59)
         except ValueError:
            pass

    data = []
    now = datetime.now()
    
    for r in Resource.query.all():
        hours = 0
        upcoming_count = 0
        
        allocs = Allocation.query.filter_by(resource_id=r.id).all()
        for a in allocs:
            e = Event.query.get(a.event_id)
            
            # Upcoming Bookings Logic
            if e.start_time > now:
                upcoming_count += 1
            
            # Utilization Logic (filtered by date)
            # If a range is provided, only count overlapping hours
            # Overlap = max(0, min(e.end, range.end) - max(e.start, range.start))
            
            if start_date and end_date:
                # Check for overlap
                latest_start = max(e.start_time, start_date)
                earliest_end = min(e.end_time, end_date)
                delta = (earliest_end - latest_start).total_seconds()
                if delta > 0:
                    hours += delta / 3600
            else:
                # No filter, total hours
                hours += (e.end_time - e.start_time).total_seconds() / 3600
                
        data.append({
            'resource': r, 
            'hours': round(hours, 1), 
            'upcoming': upcoming_count
        })
        
    return render_template('report.html', data=data, 
                         start_date=start_date_str if start_date_str else '', 
                         end_date=end_date_str if end_date_str else '')

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    # Find allocations for this event
    allocations = Allocation.query.filter_by(event_id=event_id).all()
    for alloc in allocations:
        db.session.delete(alloc)
    
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully. You can now retry allocation.')
    return redirect('/allocate')

if __name__ == '__main__':
    app.run(debug=True)
