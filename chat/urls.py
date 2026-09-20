"""
HTTP URL routing for the chat app.
"""

from django.urls import path
from . import views, friend_views, post_views, dm_views, story_views, notification_views, profile_views, search_views, report_views

app_name = 'chat'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # News
    path('news/', views.news_feed, name='news'),

        # Search
    path('search/', search_views.search, name='search'),

    # Rooms
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/new/', views.room_create, name='room_create'),
    path('rooms/<slug:slug>/', views.room_detail, name='room_detail'),

    # Friends
    path('friends/', friend_views.friends_home, name='friends_home'),
    path('friends/add/<str:username>/', friend_views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:friendship_id>/', friend_views.accept_friend_request, name='accept_friend_request'),
    path('friends/decline/<int:friendship_id>/', friend_views.decline_friend_request, name='decline_friend_request'),
    path('friends/remove/<str:username>/', friend_views.remove_friend, name='remove_friend'),

    # Profiles
    path('u/<str:username>/', friend_views.profile, name='profile'),

    # Posts / Feed
    path('feed/', post_views.feed, name='feed'),
    path('feed/new/', post_views.create_post, name='create_post'),
    path('feed/<int:post_id>/like/', post_views.toggle_like, name='toggle_like'),
    path('feed/<int:post_id>/comment/', post_views.add_comment, name='add_comment'),
    path('feed/<int:post_id>/delete/', post_views.delete_post, name='delete_post'),

    # Direct messages
    path('dm/', dm_views.inbox, name='dm_inbox'),
    path('dm/<str:username>/', dm_views.conversation, name='dm'),

    # Stories
    path('stories/new/', story_views.create_story, name='create_story'),
    path('stories/<int:story_id>/', story_views.view_story, name='view_story'),
    path('stories/<int:story_id>/delete/', story_views.delete_story, name='delete_story'),

        # Notifications
    path('api/notifications/', notification_views.list_notifications, name='notifications_list'),
    path('api/notifications/unread/', notification_views.unread_count, name='notifications_unread'),
    path('api/notifications/mark-read/', notification_views.mark_all_read, name='notifications_mark_read'),
    path('notifications/<int:notification_id>/open/', notification_views.open_notification, name='open_notification'),

        # Settings
    path('settings/profile/', profile_views.profile_settings, name='profile_settings'),
    path('settings/account/', profile_views.account_settings, name='account_settings'),
    path('settings/password/', profile_views.change_password, name='change_password'),

        # Reports / moderation
    path('report/post/<int:post_id>/', report_views.report_post, name='report_post'),
    path('report/user/<str:username>/', report_views.report_user, name='report_user'),
    path('report/comment/<int:comment_id>/', report_views.report_comment, name='report_comment'),
    path('reports/mine/', report_views.my_reports, name='my_reports'),
]

# (Append these routes to your urlpatterns list)
