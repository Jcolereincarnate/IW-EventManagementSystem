from django.db import models
from django.contrib.auth.models import User

class AdminProfile(models.Model):
    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),
        ("event_admin", "Event Admin"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="event_admin")
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    
class Attendee(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    event = models.CharField(blank=True, null= True)
    attended = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.email}"


class Event(models.Model):
    EVENT_STATUS = [
        ("Upcoming","Upcoming"),
        ("Active","Active"),
        ("Past","Past"),
        
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField( null=True)
    location = models.CharField(max_length=255)
    attendees = models.ManyToManyField(Attendee, blank=True, related_name="events")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events_created")
    status = models.CharField(choices=EVENT_STATUS, default="Upcoming")
    

    def __str__(self):
        return self.title