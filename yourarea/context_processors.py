from .models import Notification

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
