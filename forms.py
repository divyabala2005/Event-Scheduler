from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SelectField, SubmitField
from wtforms.validators import DataRequired

class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    start_time = DateTimeField("Start Time", format="%Y-%m-%dT%H:%M")
    end_time = DateTimeField("End Time", format="%Y-%m-%dT%H:%M")
    description = StringField("Description")
    submit = SubmitField("Add Event")

class ResourceForm(FlaskForm):
    name = StringField("Resource Name", validators=[DataRequired()])
    type = SelectField("Type", choices=[
        ("Room", "Room"),
        ("Instructor", "Instructor"),
        ("Equipment", "Equipment")
    ])
    submit = SubmitField("Add Resource")
class AllocationForm(FlaskForm):
    event_id = SelectField("Event", coerce=int, validators=[DataRequired()])
    resource_id = SelectField("Resource", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Allocate Resource")
