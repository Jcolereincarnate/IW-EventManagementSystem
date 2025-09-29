from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
from .models import *
from datetime import date as dated
from django.core.mail import send_mail
from django.contrib import messages
from .utils import *
import uuid
import csv
from django.http import HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.staticfiles.storage import staticfiles_storage
def check_admin(user):
    return hasattr(user, "admin_profile")

def initial_signup(request):
    event = Event.objects.filter(status__in=["Upcoming", "Active"])
    year = dated.today().year
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        organization = request.POST.get("organization")
        event_id = request.POST.get("event")
        title = request.POST.get("title")
        other_title = request.POST.get("other_title")

        if title == "Other" and other_title:
            title = other_title
        
        events = Event.objects.get(id=event_id)
        if events.date < dated.today():
            return render(request, "events/eventsignup.html", {"error": "Cannot register for past events.", "event": event})
        duplicate_exists = Attendee.objects.filter(
            name=name,
            email=email,
            phone=phone,
            event=events,
        ).exists()
        if duplicate_exists:
           return render(request, "events/eventsignup.html", {"caution": "You are already registered for this event.", "event": event})
       
        attendee = Attendee.objects.create(
            name=name,
            email=email,
            phone=phone,
            organization=organization,
            event=events,
            title=title,
        )
        logo_url = request.build_absolute_uri(staticfiles_storage.url('images/logo.png'))
        events.attendees.add(attendee)
        subject = "Registration Notification"
        from_email=settings.DEFAULT_FROM_EMAIL
        to_email = attendee.email
        context = {"events": events,
                   "name": name,
                   "email": email,
                   "phone": phone,
                   "organization": organization,
                   "title": title,
                   "logo_url": logo_url
                   }
        html_content = render_to_string("email/register_confirm.html", context)
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return render(request, "events/eventsignup.html", {"success": "You have sucessfully signed up for this event. Payment and Ticket details would be communicated to you via email", "event": event})
        
    return render(request, "events/eventsignup.html", {"event": event, "now": year})


def event_confirmation(request):
    return render(request, "events/event_confirmation.html")
    
def signup(request):
    if request.user.is_authenticated and check_admin(request.user):
        return redirect("event_list")  

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        if User.objects.filter(username=username).exists():
            return render(request, "accounts/signup.html", {"error": "Username already exists."})

        user = User.objects.create_user(username=username, password=password, email=email)
        AdminProfile.objects.create(user=user, phone=phone, role="event_admin")
        login(request, user)
        return redirect("event_list")

    return render(request, "accounts/signup.html")


def login_view(request):
    if request.user.is_authenticated and check_admin(request.user):
        return redirect("event_list")  

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            return render(request, "accounts/login.html", {"error": "Both fields are required."})

        user = authenticate(request, username=username, password=password)
        if user is not None and check_admin(user):
            login(request, user)
            return redirect("event_list") 

        return render(request, "accounts/login.html", {"error": "Invalid credentials or not an admin."})

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def event_list(request):
    paginator = Paginator(Event.objects.all().order_by("date"), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if not check_admin(request.user):
        return HttpResponseForbidden("You are not authorized to view this page.")
    events = Event.objects.all().order_by("date")
    for event in events:
        if event.date < dated.today():
            event.status = "Past"
            event.save()
        if event.date == dated.today():
            event.status = "Active"
            event.save()
    total_attendees = sum(event.attendees.count() for event in events)
    upcoming_events = Event.objects.filter(status="Upcoming").count()
    for event in events:
        event.attended_count = event.attendees.filter(attended=True).count()
    context = {
        "events": events,
        "total_attendees": total_attendees,
        "upcoming_events": upcoming_events,
        "page_obj": page_obj,
    }
    return render(request, "events/event_list.html", context)


@login_required
def event_detail(request, event_id):
    if not check_admin(request.user):
        return HttpResponseForbidden("You are not authorized to view this page.")
    event = get_object_or_404(Event, id=event_id)
    verified_attendee = Attendee.objects.filter(attended=True).count()
    context= {
        "event": event,
        "verified_attendee": verified_attendee,
    }
    return render(request, "events/event_detail.html", context)


@login_required
def add_attendee(request, event_id):
    if not check_admin(request.user):
        return HttpResponseForbidden("You are not authorized to perform this action.")
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        organization = request.POST.get("organization")
        title= request.POST.get("title")

        attendee, created = Attendee.objects.get_or_create(
            event= event,
            email=email,
            defaults={"name": name, "phone": phone, "organization": organization, "title": title},
        )
        event.attendees.add(attendee)
        return redirect("event_detail", event_id=event.id)

    return render(request, "events/add_attendee.html", {"event": event})


@login_required
def add_event(request):
    if request.method == 'POST':
        title = request.POST.get("event_name")
        description = request.POST.get("desc")
        date = request.POST.get("event_date")
        time = request.POST.get("event_time")
        location = request.POST.get("event_location")
        event, created = Event.objects.get_or_create(
            title = title,
            description = description,
            date =date,
            time = time, 
            location = location,
            created_by = request.user,
        )
        return redirect("event_list")
    return render(request, "events/add_event.html", {"today" : dated.today().isoformat()})


@login_required
def view_attendees(request):
    attendees = Attendee.objects.all()
    total_attendees = attendees.count()
    organizations = Attendee.objects.values_list("organization", flat=True).distinct()
    events = Event.objects.all()
    organizations_count = organizations.count()
    q = request.GET.get("q")
    if q: 
        attendees = attendees.filter(Q(name__icontains=q) | Q(email__icontains=q))
    event_title = request.GET.get("event", "").strip()
    if event_title:
        attendees = attendees.filter(event=event_title)
    org = request.GET.get("organization")
    if org:
        attendees = attendees.filter(organization=org)
    context = {
        "attendees":attendees,
        "total_attendees": total_attendees,
        "organizations": organizations,
        "organizations_count": organizations_count,
        "events": events,
    }
    return render(request, "events/attendees.html", context)


@login_required
def edit_attendee(request, attendee_id):
    attendee = get_object_or_404(Attendee, pk=attendee_id)

    if request.method == "POST":
        attendee.name = request.POST.get("name")
        attendee.email = request.POST.get("email")
        attendee.organization = request.POST.get("organization")
        attendee.title = request.POST.get("title")
        attendee.attended = request.POST.get("attended")
        attendee.save()
        first_event = attendee.events.first()
        if first_event:
            return redirect("event_detail", first_event.id)
        else:
            return redirect("attendee_list") 

    return redirect("attendee_list")


@login_required
def remove_attendee(request, attendee_id):
    attendee = get_object_or_404(Attendee, id=attendee_id)
    attendee.delete()
    messages.success(request, "Attendee removed successfully.")
    return redirect("attendees-list") 

@login_required
def send_email_attendee(request, attendee_id):
    attendee = get_object_or_404(Attendee, id=attendee_id)
    if request.method == "POST":
        title  = request. POST.get("title")
        message = request.POST.get("message")
        link = request.POST.get("link")
    logo_url = request.build_absolute_uri(staticfiles_storage.url('images/logo.png'))
    subject =  title
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = attendee.email
    context = {"attendee": attendee,
               "message": message,
               "link": link,
               "logo_url": logo_url}
    html_content = render_to_string("email/generic_email.html", context)
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
    messages.success(request, f"Email sent to {attendee.name}.")
    return redirect("attendees-list")

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id =event_id)
    if request.method == "POST":
        event.title  = request.POST.get("title")
        event.description = request.POST.get("description")
        event.date = request.POST.get("date")
        event.time = request.POST.get("time")
        event.location = request.POST.get("location")
        event.status = request.POST.get("status")
        event.save()
    return redirect("event_list") 

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id =event_id)
    event.delete()
    messages.success(request, "Attendee removed successfully.")
    return redirect("event_list") 

'''
def event_signup(request):
    event = Event.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        organization = request.POST.get("organization")
        event_id = request.POST.get("event")
        event = Event.objects.get(id=event_id)
        attendee, created = Attendee.objects.get_or_create(
            name=name,
            email=email,
            phone=phone,
            organization=organization,
            event=event,
        )

        data = f"""
        Name: {name}
        Email: {email}
        Number: {phone}
        Organization: {organization}
        Event: {event}
        """
        filename = f"{uuid.uuid4()}.png"
        qr_path = generate_code(data, filename)
        request.session["qr_code"] = qr_path
        return redirect("event_qrcode")
    context ={
        "event": event
    }

    return render(request, "events/eventsignup.html", context)
'''

def event_signup(request):
    events = Event.objects.filter(status__in=["Upcoming", "Active"])
    if request.method == "POST":
        name = request.POST.get("name")
        event_id = request.POST.get("event")
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return render(request, "events/qrcodesignup.html", {
                "events": events,
                "error": "Selected event does not exist."
            })

        attendee = Attendee.objects.filter(name=name, event=event).first()
        if not attendee:
            return render(request, "events/qrcodesignup.html", {
                "events": events,
                "error": "Attendee not found for this event."
            })

        email = attendee.email
        phone = attendee.phone
        organization = attendee.organization
        title = attendee.title

        data_dict = {
            "name": name,
            "email": email,
            "phone": phone,
            "organization": organization,
            "event": event.title,
            "title": title,
        }

        data = "\n".join([
            data_dict["name"],
            data_dict["email"],
            data_dict["phone"],
            data_dict["organization"],
            data_dict["event"],
            data_dict["title"],
        ])

        checkin_url = request.build_absolute_uri(
            reverse("event_checkin", args=[attendee.id])
        )
        filename = f"{uuid.uuid4()}_{name}.png"
        qr_path = generate_code(
            checkin_url,
            filename,
            logo_path="eventapp/static/images/normalimage.png"
        )

        request.session["qr_code"] = qr_path
        request.session["event_id"] = event_id
        request.session["attendee_id"] = attendee.id
        request.session["data_dict"] = data_dict

        return redirect("event_qrcode")
    return render(request, "events/qrcodesignup.html", {"events": events})


def individual_qrcode(request):
    qr_code = request.session.get("qr_code", None)
    event_id = request.session.get("event_id", None)
    data_dict =request.session.get("data_dict", None)
    if event_id is None:
        return render(request, "events/errorpage.html")
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return render(request, "events/errorpage.html")
    name = data_dict.get("name")
    email= data_dict.get("email")
    phone = data_dict.get("phone")
    organization = data_dict.get("organization")
    title = data_dict.get("title")
    context = {
        "qr_code": qr_code,
        "event" : event,
        "name": name,
        "email": email,
        "phone": phone,
        "organization": organization,
        "title": title,
    }
    
    return render(request, "events/qrcode.html", context)


def add_attendees(request):
    
    return(render(request, "events/add_attendee.html"))



def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendees.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Organization', 'Event'])

    attendees = Attendee.objects.all()
    for attendee in attendees:
        events = ", ".join([event.title for event in attendee.events.all()])
        writer.writerow([attendee.name, attendee.email, attendee.phone, attendee.organization, events])

    return response   


def export_event_csv(request, event_id):
    events = get_object_or_404(Event, id=event_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{events.title} Attendees.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Organization', 'Event'])

    attendees = events.attendees.all()
    for attendee in attendees:
        writer.writerow([attendee.name, attendee.email, attendee.phone, attendee.organization])

    return response   

def event_checkin(request, attendee_id):
    attendee = get_object_or_404(Attendee, id=attendee_id)
    attendee.attended = True
    attendee.save()

    messages.success(request, f"{attendee.name} checked in successfully for {attendee.event.title}")
    return render(request, "events/checkin_success.html", {"attendee": attendee})

'''      
    
def event_signup(request):
    event = Event.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        organization = request.POST.get("organization")
        event_id = request.POST.get("event")
        title = request.POST.get("title")
        other_title = request.POST.get("other_title")

        if title == "Other" and other_title:
            title = other_title
        
        
        events = Event.objects.get(id=event_id)
        if events.date < dated.today():
            messages.error(request, "Cannot register for past events.")
            return redirect("event_signup")
        data_dict = {
            "name": name,
            "email": email,
            "phone": phone,
            "organization": organization,
            "event": events.title,
            "title": title,
            }
        
        data = "\n".join([data_dict["name"],data_dict["email"],data_dict["phone"],data_dict["organization"],data_dict["event"], data_dict["title"]])

        filename = f"{uuid.uuid4()}_{name}.png"
        qr_path = generate_code(data, filename, logo_path = "eventapp/static/images/normalimage.png")
        request.session["qr_code"] = qr_path
        request.session["event_id"] = event_id
        request.session["data_dict"] = data_dict
        
        duplicate_exists = Attendee.objects.filter(
        name=name,
        email=email,
        phone=phone,
        organization=organization,
        event=events,
        title=title,).exists()
        if duplicate_exists:
            messages.warning(request, "You are already registered for this event.")
            return redirect("event_qrcode")
        attendee = Attendee.objects.create(
            name=name,
            email=email,
            phone=phone,
            organization=organization,
            event=events,
            title=title,
        )
        events.attendees.add(attendee)

      
        print(request.session.items())
        return redirect("event_qrcode")

    return render(request, "events/eventsignup.html", {"event": event})

def individual_qrcode(request):
    qr_code = request.session.get("qr_code", None)
    event_id = request.session.get("event_id", None)
    data_dict =request.session.get("data_dict", None)
    if event_id is None:
        return render(request, "events/errorpage.html")
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return render(request, "events/errorpage.html")
    name = data_dict.get("name")
    email= data_dict.get("email")
    phone = data_dict.get("phone")
    organization = data_dict.get("organization")
    title = data_dict.get("title")
    context = {
        "qr_code": qr_code,
        "event" : event,
        "name": name,
        "email": email,
        "phone": phone,
        "organization": organization,
        "title": title,
    }
    
    return render(request, "events/qrcode.html", context)
'''