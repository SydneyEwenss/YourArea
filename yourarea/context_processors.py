from .models import Notification, Event, Group
from .forms import PostForm

def notifications(request):
    if request.user.is_authenticated:
        # Get the count of unread notifications for the user
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications_count': unread_count
        }
    return {
        'unread_notifications_count': 0
    }

def sidebar_events(request):
    if request.user.is_authenticated:
        # Get the groups where the user is a member
        user_groups = Group.objects.filter(members=request.user)

        # Get events for these groups
        events = Event.objects.filter(group__in=user_groups).order_by('date')[:5]
    else:
        events = []  # If not authenticated, no events
    
    return {'sidebar_events': events}

def post_form(request):
    return {'post_form': PostForm()}