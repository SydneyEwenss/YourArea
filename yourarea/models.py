from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill, ResizeToFit
import re

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} received a notification ({self.created:%d-%m-%Y %H:%M}): {self.message}'
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False, blank=True)
    date_modified = models.DateTimeField(User, auto_now=True)

    profile_image = ProcessedImageField(
        upload_to='profile_images/',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 80},
        null=True,
        blank=True,
        default='default-profile.jpg'
    )
    display_name = models.CharField(max_length=30, blank=True)
    background_image = ProcessedImageField(
        upload_to='profile_background_images/',
        processors=[ResizeToFill(1920, 1080)],
        format='JPEG',
        options={'quality': 80},
        null=True,
        blank=True,
    )
    bio = models.CharField(max_length=280, blank=True)
    pronouns = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        user_profile.follows.set([instance.profile.id])
        user_profile.save()

class Group(models.Model):
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    moderators = models.ManyToManyField(User, related_name='moderated_groups', blank=True)
    members = models.ManyToManyField(User, related_name='member_groups', blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    group_image = ProcessedImageField(
        upload_to='group_images/',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 80},
        null=True,
        blank=True,
    )
    background_image = ProcessedImageField(
        upload_to='group_background_images/',
        processors=[ResizeToFill(1920, 1080)],
        format='JPEG',
        options={'quality': 80},
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Post(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, related_name="posts", on_delete=models.CASCADE)
    mentions = models.ManyToManyField(User, related_name='mentioned_in', blank=True)

    content = models.CharField(max_length=280)
    media = models.FileField(upload_to='post_media/', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_posts', blank=True)
    
    
    def total_likes(self):
        return self.likes.count()
    
    def total_dislikes(self):
        return self.dislikes.count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the post first to get its ID
        mentioned_usernames = extract_mentions(self.content)
        mentioned_users = User.objects.filter(username__in=mentioned_usernames)
        self.mentions.set(mentioned_users)

        for user in mentioned_users:
            Notification.objects.create(
                user=user,
                title=f'Mentioned in post by {self.user.username}',
                message=f'You were mentioned in a post by {self.user.username}.',
                action_url=f'/post/{self.id}'
            )

    def __str__(self):
        return f'{self.user.username} ({self.created:%d-%m-%Y %H:%M}): {self.content}'
    
def extract_mentions(content):
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, content)
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.CharField(max_length=280)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} commented on {self.post.user.username}\'s post ({self.created:%d-%m-%Y %H:%M}): {self.content}'
    
class Event(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=50, blank=True, null=True) 
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} ({self.date:%d-%m-%Y %H:%M})'
    
class News(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} ({self.created:%d-%m-%Y %H:%M})'
    
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} liked {self.post.user.username}\'s post ({self.created:%d-%m-%Y %H:%M})'
    
class Dislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} disliked {self.post.user.username}\'s post ({self.created:%d-%m-%Y %H:%M})'
    
