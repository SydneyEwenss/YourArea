from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from .models import Post, Profile, Comment
from .forms import *
from .utils import *

from django.http import JsonResponse
from django.core.paginator import Paginator

def home(request):
    tab = request.GET.get('tab', 'all')
    
    if request.user.is_authenticated:
        if tab == 'following':
            posts = Post.objects.filter(user__profile__in=request.user.profile.follows.all()).order_by('-created')
            posts = posts | Post.objects.filter(group__members=request.user).order_by('-created')
            posts = posts.distinct()  # Remove duplicates
        else:
            posts = Post.objects.all().order_by('-created')

        # Linkify the post content
        for post in posts:
            post.content = linkify_mentions(post.content)

        # Paginate posts
        paginator = Paginator(posts, 20)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Render posts with the post_list template
            html = render_to_string('post_list.html', {'posts': page_obj})
            return JsonResponse({'html': html})

        return render(request, 'home.html', {'posts': page_obj})

    else:
        # Handle when the user is not authenticated
        posts = Post.objects.all().order_by('-created')
        paginator = Paginator(posts, 20)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)

        return render(request, 'home.html', {'posts': page_obj})
    
from django.http import JsonResponse

def load_more_posts(request):
    # Get the next page number from the request
    page = request.GET.get('page', 1)
    # Fetch posts for that page (adjust this query based on your pagination logic)
    posts = Post.objects.all()[10 * (int(page) - 1): 10 * int(page)]
    
    # Check if posts are available
    if posts:
        # Return posts in JSON format
        post_data = [{'id': post.id, 'content': post.content, 'created_at': post.created} for post in posts]
        return JsonResponse({'posts': post_data})
    else:
        # Return empty posts array if no posts are found
        return JsonResponse({'posts': []})
    
def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials.')
            return redirect('login')
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'You have successfully registered.')
            return redirect('home')
    return render(request, 'register.html', {'form': form})

def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    posts = Post.objects.filter(user__username=username).order_by('-created')
    if request.user.is_authenticated:
        if request.method == "POST":
            current_user_profile = request.user.profile
            action = request.POST['follow']
            if action == 'follow':
                current_user_profile.follows.add(profile)
            else:
                current_user_profile.follows.remove(profile)
            current_user_profile.save()

    return render(request, 'profile.html', {'profile': profile, 'posts': posts})

def followers(request, pk):
    profiles = Profile.objects.filter(followed_by=pk)
    return render(request, 'profile_list.html' , {'profiles': profiles})

def following(request, pk):
    profiles = Profile.objects.filter(follows=pk)
    return render(request, 'profile_list.html' , {'profiles': profiles})

def update_profile(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        profile = Profile.objects.get(user__id=request.user.id)
        user_form = SignUpForm(request.POST or None, instance=current_user)
        profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            login(request, current_user)
            messages.success(request, 'Profile updated successfully.')
            return redirect('area', username=current_user.username)
        return render(request, 'update_profile.html', {'user_form': user_form, 'profile_form': profile_form})
    else:
        messages.error(request, 'You must be logged in to view this page.')
        return redirect('home')
    
def post(request, pk):
    post = get_object_or_404(Post, id=pk)
    if post:
        comments = Comment.objects.filter(post=post).order_by('-created')
        if request.method == "POST":
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user = request.user
                comment.post = post
                comment.save()
                create_notification(
                    user=post.user,
                    title=f"{request.user.username} commented on your post",
                    message=comment.content
                )
                messages.success(request, 'Comment added successfully.')
                return redirect('post', pk=pk)
        else:
            form = CommentForm()
        return render(request, 'post.html', {'post': post, 'comments': comments, 'form': form})
    else:
        messages.error(request, 'Post not found.')
        return redirect('home')
    
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user.is_authenticated:
        # If the user is not in the 'likes' list, add the like
        if request.user not in post.likes.all():
            post.likes.add(request.user)
            liked = True
            create_notification(
                user=post.user,
                title=f"{request.user.username} liked your post",
                message=post.content
            )
        else:
            # If the user has already liked the post, remove the like
            post.likes.remove(request.user)
            liked = False
        
        # Save the post after adding or removing the like
        post.save()

        # Return the total likes and whether the user liked or unliked the post
        return JsonResponse({
            'total_likes': post.total_likes(),
            'liked': liked  # True if liked, False if unliked
        })
    else:
        # User is not authenticated, return an error message
        return JsonResponse({'error': 'User not authenticated'}, status=400)
    
def dislike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user.is_authenticated:
        # If the user is not in the 'dislikes' list, add the dislike
        if request.user not in post.dislikes.all():
            post.dislikes.add(request.user)
            disliked = True
            create_notification(
                user=post.user,
                title=f"{request.user.username} disliked your post",
                message=post.content
            )
        else:
            # If the user has already disliked the post, remove the dislike
            post.dislikes.remove(request.user)
            disliked = False
        
        # Save the post after adding or removing the dislike
        post.save()

        # Return the total dislikes and whether the user disliked or undisliked the post
        return JsonResponse({
            'total_dislikes': post.total_dislikes(),
            'disliked': disliked  # True if disliked, False if undisliked
        })
    else:
        # User is not authenticated, return an error message
        return JsonResponse({'error': 'User not authenticated'}, status=400)
    
def delete_post(request, pk):
    if request.user.is_authenticated:
        post = get_object_or_404(Post, id=pk)
        if request.user.username == post.user.username:
            post.delete()
            messages.success(request, 'Post deleted successfully.')
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'You do not have permission to delete this post.')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'You must be logged in to delete a post.')
        return redirect(request.META.get('HTTP_REFERER'))
    
def notifications(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created')
        read_notifications = Notification.objects.filter(user=request.user, is_read=True).order_by('-created')
        action_required_notifications = Notification.objects.filter(user=request.user, is_read=False, action_url__isnull=False).order_by('-created')

        context = {
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
            'action_required_notifications': action_required_notifications,
            'unread_notifications_count': unread_notifications.count()
        }
        return render(request, 'notifications.html', context)
    else:
        messages.error(request, 'You must be logged in to view notifications.')
        return redirect('home')
    
def mark_as_read(request, notification_id):
    if request.user.is_authenticated:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('notifications')
    else:
        messages.error(request, 'You must be logged in to mark notifications as read.')
        return redirect('home')
    
def delete_notification(request, notification_id):
    if request.user.is_authenticated:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.delete()
        return redirect('notifications')
    else:
        messages.error(request, 'You must be logged in to delete notifications.')
        return redirect('home')
    
def create_notification(user, title, message, action_url=None):
    Notification.objects.create(user=user, title=title, message=message, action_url=action_url)

def groups_list(request):
    groups = Group.objects.all().order_by('-date_created')  # Fetch all groups
    return render(request, 'groups/groups_list.html', {'groups': groups})


def create_group(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = GroupForm(request.POST or None, request.FILES or None)
            if form.is_valid():
                group = form.save(commit=False)
                group.owner = request.user
                group.save()
                group.moderators.add(request.user)
                group.members.add(request.user)
                group.save()
                messages.success(request, 'Group created successfully.')
                return redirect('group', slug = group.slug)
        else:
            form = GroupForm()
        return render(request, 'groups/create_group.html', {'form': form})
    
def group(request, slug):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, slug = slug)
        posts = Post.objects.filter(group=group).order_by('-created')
        events = Event.objects.filter(group=group).order_by('-created')
        news = News.objects.filter(group=group).order_by('-created')

        form = PostForm(request.POST or None, request.FILES or None)
        if request.method == "POST":
            if 'join_group' in request.POST:
                group.members.add(request.user)
                messages.success(request, 'You have successfully joined the group.')
            elif 'leave_group' in request.POST:
                group.members.remove(request.user)
                messages.success(request, 'You have successfully left the group.')
            elif form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.group = group
                post.save()
                print(request.FILES)
                messages.success(request, 'Post created successfully.')
                return redirect('group' , slug = group.slug)
    
        return render(request, 'groups/group.html', {'group': group, 'posts': posts, 'events': events, 'news': news, 'form': form})
    
def join_group(request, slug):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, slug = slug)
        if request.user not in group.members.all():
            group.members.add(request.user)
            group.save()
            messages.success(request, 'You have successfully joined the group.')
        else:
            messages.error(request, 'You are already a member of this group.')
        return redirect('group', slug = group.slug)
    
def leave_group(request, slug):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, slug = slug)
        if request.user in group.members.all():
            group.members.remove(request.user)
            group.save()
            messages.success(request, 'You have successfully left the group.')
        else:
            messages.error(request, 'You are not a member of this group.')
        return redirect('group', slug = group.slug)
    
def update_group(request, slug):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, slug = slug)
        if request.user == group.owner:
            if request.method == "POST":
                form = GroupForm(request.POST or None, request.FILES or None, instance=group)
                if 'delete_group' in request.POST:
                    group.delete()
                    messages.success(request, 'Group deleted successfully.')
                    return redirect('groups_list')
                elif form.is_valid():
                    form.save()
                    messages.success(request, 'Group updated successfully.')
                    return redirect('group', slug = group.slug)
            else:
                form = GroupForm(instance=group)
            return render(request, 'groups/update_group.html', {'form': form})
        else:
            messages.error(request, 'You do not have permission to update this group.')
            return redirect('group', slug = group.slug)
        
def search(request):
    query = request.GET.get('query', '')  # Get query parameter, default to empty string if not present
    posts = Post.objects.filter(content__icontains=query) if query else []
    profiles = Profile.objects.filter(display_name__icontains=query) if query else []
    groups = Group.objects.filter(name__icontains=query) if query else []

    return render(request, 'search.html', {
        'query': query,
        'posts': posts,
        'profiles': profiles,
        'groups': groups,
    })

def profiles_list(request):
    profiles = Profile.objects.all().order_by('-user__date_joined')
    return render(request, 'profile_list.html', {'profiles': profiles})

def create_event(request, slug):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = EventForm(request.POST or None)
            if form.is_valid():
                event = form.save(commit=False)
                event.group = Group.objects.get(slug=slug)
                event.save()
                messages.success(request, 'Event created successfully.')
                return redirect('group', slug = event.group.slug)
        else:
            form = EventForm()
        return render(request, 'groups/create_event.html', {'form': form})
    
def post_create(request):
    if request.user.is_authenticated:
        form = PostForm(request.POST, request.FILES)

        if request.method == "POST":
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                messages.success(request, 'Post created successfully.')
                # Return JSON response indicating success
                return JsonResponse({'success': True})
            else:
                # Return validation errors
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        messages.error(request, 'You must be logged in to create a post.')
        return redirect('home')
    