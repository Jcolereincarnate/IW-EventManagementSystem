from .import views
from django.urls import path

urlpatterns= [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    #path("", views.index, name="index"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("add-event/", views.add_event, name="add_event"),
    path("events/<int:event_id>/add-attendee/", views.add_attendee, name="add_attendee"),   
    path("attendees-list/", views.view_attendees, name = "attendees-list"),
    path("events/<int:attendee_id>/edit/", views.edit_attendee, name = "edit_attendee"),
    path("events/<int:attendee_id>/remove/", views.remove_attendee, name="remove_attendee"),
    path("events/<int:attendee_id>/email/", views.send_email_attendee, name="send_email_attendee"),
    path("events/<int:event_id>/edit", views.edit_event, name="edit-event"),
    path("events/<int:event_id>/delete", views.delete_event, name="delete-event"),
    path("event_signup", views.event_signup, name = "event-signup"),
    path("events/qrcode/", views.individual_qrcode, name = "event_qrcode"),
    path("events/", views.add_attendees, name = "add_attendees"),
    path("events/csv/", views.export_csv, name = "export_csv"),
    path("events/<int:event_id>/csv/", views.export_event_csv, name = "export_event_csv"),
    path("event/checkin/<int:attendee_id>/", views.event_checkin, name="event_checkin"), 
    path("", views.initial_signup, name="initial_signup"),
    path("event/event_confirmation/", views.event_confirmation, name="event_confirmation"),
]