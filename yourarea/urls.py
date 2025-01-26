from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('@<str:username>', views.profile, name='area'),
    path('area/followers/<int:pk>/', views.followers, name='followers'),
    path('area/following/<int:pk>/', views.following, name='following'),
    path('update_area/', views.update_profile, name='update_area'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('dislike-post/<int:post_id>/', views.dislike_post, name='dislike_post'),
    path('post/<int:pk>/', views.post, name='post'),
    path('delete-post/<int:pk>/', views.delete_post, name='delete_post'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-as-read/<int:notification_id>', views.mark_as_read, name='mark_as_read'),
    path("notifications/delete/<int:notification_id>/", views.delete_notification, name="delete_notification"),
    path('groups/', views.groups_list, name='groups_list'),
    path('group/create', views.create_group, name='create_group'),
    path('group/<slug:slug>', views.group, name='group'),
    path('group/<slug:slug>/join', views.join_group, name='join_group'),
    path('group/<slug:slug>/leave', views.leave_group, name='leave_group'),
    path('group/<slug:slug>/update', views.update_group, name='update_group'),
    path('group/<slug:slug>/create-event', views.create_event, name='create_event'),
    path('search/', views.search, name='search'),
    path('areas/', views.profiles_list, name='areas_list'),
]
