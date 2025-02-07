from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Count, F, Q, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta
from .models import Post, Profile, Comment
from .forms import *
from .utils import *

def home(request):
    tab = request.GET.get('tab', 'all')
    page_number = request.GET.get('page') or 1
    page_number = int(page_number)
    form = None

    if request.user.is_authenticated:
        recommended_posts = get_recommended_posts(request.user, page_number)

        if tab == 'following':
            posts = Post.objects.filter(user__profile__in=request.user.profile.follows.all()).order_by('-created')
            posts = posts | Post.objects.filter(group__members=request.user).order_by('-created')
            posts = posts.distinct()
        else:
            posts = recommended_posts

        for post in posts:
            post.content = linkify_mentions(post.content)

        form = PostForm(request.POST or None, request.FILES or None)
        if request.method == "POST":
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                messages.success(request, 'Post created successfully.')
            else:
                messages.error(request, 'There was an error making this post')

    else:
        posts = Post.objects.all().order_by('-created')

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('post_list.html', {'posts': page_obj})

        if not html.strip():
            return JsonResponse({'html': ''})

        return JsonResponse({'html': html})

    return render(request, 'home.html', {'posts': page_obj, 'form': form})

def get_recommended_posts(user, page_number=1, page_size=10):
    current_time = timezone.now()
    user_interests = user.profile.interests.all()

    recommended_posts = Post.objects.filter(tags__in=user_interests).distinct()
    recommended_posts = recommended_posts.annotate(
        like_count=Count('likes__id'),
        recency_weight=ExpressionWrapper(
            current_time - F('created'),
            output_field=fields.FloatField()
        )
    ).annotate(
        recency_seconds = F('recency_weight')
    ).annotate(
        score = F('like_count') * 3 - F('recency_seconds') * 0.1
    )

    followed_users_posts = Post.objects.filter(user__profile__in=user.profile.follows.all()).distinct()
    followed_users_posts = followed_users_posts.annotate(
        like_count=Count('likes__id'),
        recency_weight=ExpressionWrapper(
            current_time - F('created'),
            output_field=fields.FloatField()
        )
    ).annotate(
        recency_seconds = F('recency_weight')
    ).annotate(
        score = F('like_count') * 2 - F('recency_seconds') * 0.1
    )

    followed_group_posts = Post.objects.filter(group__members=user).distinct()
    followed_group_posts = followed_group_posts.annotate(
        like_count=Count('likes__id'),
        recency_weight=ExpressionWrapper(
            current_time - F('created'),
            output_field=fields.FloatField()
        )
    ).annotate(
        recency_seconds = F('recency_weight')
    ).annotate(
        score = F('like_count') * 1 - F('recency_seconds') * 0.1
    )

    all_recommendations = recommended_posts | followed_users_posts | followed_group_posts
    all_recommendations = all_recommendations.order_by('-score', '-created')

    paginator = Paginator(all_recommendations, page_size)
    page_obj = paginator.get_page(page_number)

    return page_obj

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, 'You have successfully logged in.')
                return redirect('home')
            else:
                messages.error(request, 'Your account has not been activated. Check your emails.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid login credentials.')
            return redirect('login')
    return render(request, 'auth/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.is_active = False
            user.save()

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            link = f"http://{domain}/activate/{uid}/{token}/"

            subject = "Confirm Your Email Address"
            message = render_to_string('emails/confirmation_email.html', {'user': user, 'link': link})

            send_mail(subject, message, 'sydneyewens06@gmil.com', [user.email])

            return render(request, 'emails/check_email.html')
    return render(request, 'auth/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Your account has been activated.")
        return redirect('home')
    else:
        messages.error(request, "Invalid activation link.")
        return redirect('login')
    
def password_reset_request(request):
    form = PasswordResetForm()
    
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                domain = request.get_host()
                link = f"http://{domain}/password_reset_confirm/{uid}/{token}/"

                subject = "Reset Your Password"
                message = render_to_string('emails/password_reset_email.html', {'user': user, 'link': link})

                send_mail(subject, message, 'sydneyewens06@gmail.com', [user.email])

            return render(request, "emails/password_reset_sent.html")

    return render(request, "auth/password_reset.html", {"form": form})
    
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data["new_password1"])
                user.save()
                return redirect("password_reset_complete")
        else:
            form = SetPasswordForm()
        return render(request, "auth/password_reset_confirm.html", {"form": form})
    else:
        return render(request, "auth/password_reset_invalid.html")

def password_reset_complete(request):
    return render(request, "auth/password_reset_complete.html")

def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    posts = Post.objects.filter(user__username=username).order_by('-created')
    if request.user.is_authenticated:
        if request.method == "POST":
            current_user_profile = request.user.profile
            action = request.POST['follow']
            if action == 'follow':
                if current_user_profile != profile:
                    current_user_profile.follows.add(profile)
                    create_notification(
                        user=profile.user,
                        title=f"{request.user.username} followed you",
                        action_url=reverse('area', args=[profile.user.username])
                    )
                else:
                    messages.error(request, "You can't follow yourself")
            else:
                if current_user_profile != profile:
                    current_user_profile.follows.remove(profile)
                    create_notification(
                        user=profile.user,
                        title=f"{request.user.username} unfollowed you",
                        action_url=reverse('area', args=[profile.user.username])
                    )
                else:
                    messages.error(request, "You can't unfollow yourself")
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
                if comment.user != post.user:
                    create_notification(
                        user=post.user,
                        title=f"{request.user.username} commented on your post",
                        message=comment.content,
                        action_url=reverse('post', args=[post.id])
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
            if post.user != request.user:
                create_notification(
                    user=post.user,
                    title=f"{request.user.username} liked your post",
                    message=post.content,
                    action_url=reverse('post', args=[post_id])
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
        messages.error(request, "You must be logged in to like posts")
        return JsonResponse({'error': 'User not authenticated'}, status=400)
    
def dislike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user.is_authenticated:
        # If the user is not in the 'dislikes' list, add the dislike
        if request.user not in post.dislikes.all():
            post.dislikes.add(request.user)
            disliked = True
            if post.user != request.user:
                create_notification(
                    user=post.user,
                    title=f"{request.user.username} disliked your post",
                    message=post.content,
                    action_url=reverse('post', args=[post_id])
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

        context = {
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
            'unread_notifications_count': unread_notifications.count()
        }
        return render(request, 'notifications.html', context)
    else:
        messages.error(request, 'You must be logged in to view notifications.')
        return redirect('home')
    
def mark_as_read(request, notification_id=None):
    if request.user.is_authenticated:
        if request.method == 'POST' and notification_id is None:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
        
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('notifications')

    messages.error(request, 'You must be logged in to mark notifications as read.')
    return redirect('home')
    
def create_notification(user, title, message=None, action_url=None):
    time_threshold = timezone.now() - timedelta(minutes = 60)

    recent_notification_exists = Notification.objects.filter(
        user=user,
        title=title,
        message=message,
        created__gte=time_threshold
    ).exists()

    if not recent_notification_exists:
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
    group = get_object_or_404(Group, slug = slug)
    posts = Post.objects.filter(group=group).order_by('-created')
    events = Event.objects.filter(group=group).order_by('-created')
    news = News.objects.filter(group=group).order_by('-created')

    form = None

    if request.user.is_authenticated:
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
    profiles = Profile.objects.filter(Q(display_name__icontains=query) | Q(user__username__icontains=query)) if query else []
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
    