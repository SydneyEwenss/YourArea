from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import *

class PostForm(forms.ModelForm):
    content = forms.CharField(required=True, widget=forms.Textarea(
        attrs={
            'placeholder': "What's on your mind?",
            'class': 'form-control',
            }
            ),
            label=''
        )
    media = forms.FileField(required=False, widget=forms.FileInput(
        attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*',
            }
    ), label='')
    
    class Meta:
        model = Post
        fields = ('content', 'media',)

    def clean_media(self):
        media = self.cleaned_data.get('media')

        if media:
            # Check the file type here
            if not media.name.endswith(('.mp4', '.webm', '.ogg', '.jpg', '.jpeg', '.png', '.gif')):
                raise forms.ValidationError('Invalid file format. Allowed formats are .mp4, .webm, .ogg, .jpg, .jpeg, .png, .gif')
        
        return media

class CommentForm(forms.ModelForm):
    content = forms.CharField(required=True, widget=forms.Textarea(
        attrs={
            'placeholder': 'Add a comment...',
            'class': 'form-control',
            }
            ),
            label=''
        )
    
    class Meta:
        model = Comment
        exclude = ('user', 'post',)

class ProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(label="Profile picutre", required=False, widget=forms.FileInput)
    display_name = forms.CharField(label="Display name", required=False, widget=forms.TextInput)
    background_image = forms.ImageField(label="Background image", required=False, widget=forms.FileInput)
    bio = forms.CharField(label="Bio", required=False, widget=forms.Textarea)
    pronouns = forms.CharField(label="Pronouns", required=False, widget=forms.TextInput)

    class Meta:
        model = Profile
        fields = ('profile_image', 'display_name', 'background_image', 'bio', 'pronouns')

class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={
            'placeholder': 'Email',
            'class': 'form-control',
            }
            ),
            label=''
        )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['username'].label = 'Username'
        self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'
        
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = 'Password'
        self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can’t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can’t be a commonly used password.</li><li>Your password can’t be entirely numeric.</li></ul>'
        
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Password confirmation'
        self.fields['password2'].label = 'Password confirmation'
        self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'
        
    def clean_username(self):
        username = self.cleaned_data['username']
        username = username.lower()
        
        if not re.match(r'^[a-z0-9._]+$', username):
            raise ValidationError('Username can only contain lowercase letters, digits, periods (.), and underscores (_).')
        
        return username
    
class GroupForm(forms.ModelForm):
    name = forms.CharField(label='Group name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label='Description', required=True, widget=forms.Textarea(attrs={'class': 'form-control'}))
    group_image = forms.ImageField(label='Group image', required=True, widget=forms.FileInput)
    background_image = forms.ImageField(label='Background image', required=False, widget=forms.FileInput)

    class Meta:
        model = Group
        fields = ('name', 'description', 'group_image', 'background_image',)

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class EventForm(forms.ModelForm):
    title = forms.CharField(label='Title', widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label='Description', required=True, widget=forms.Textarea(attrs={'class': 'form-control'}))
    date = forms.DateTimeField(label='Date', widget=DateTimeInput())
    location = forms.CharField(label='Location', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Event
        fields = ('title', 'description', 'date', 'location',)

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ('title', 'content',)

class SearchForm(forms.Form):
    query = forms.CharField(label='', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search'}))
    
    def clean_query(self):
        query = self.cleaned_data['query']
        query = query.strip()
        
        if len(query) < 3:
            raise ValidationError('Search query must be at least 3 characters long.')
        
        return query