from django.conf.urls import url
from . import views

app_name = 'dropbox'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^user/(?P<username>.+)$', views.user, name='user'),
    url(r'^myprofile/$', views.my_profile, name='my_profile'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^files/$', views.files, name='files'),
    url(r'^file/(?P<filename>.+)$', views.file, name='file'),
    url(r'^changesettings/(?P<filename>.+)$', views.change_settings, name='changesettings'),
    url(r'^deletefile/(?P<filename>.+)$', views.delete_file, name='deletefile'),
    url(r'^download/(?P<filename>.+)$', views.download, name='download'),
    url(r'^groups/$', views.groups, name='groups'),
    url(r'^group/(?P<group_name>.+)/$', views.group, name='group'),
    url(r'^group/(?P<group_name>.+)/invite$', views.group_invite_member, name='group_invite_member'),
    url(r'^group/(?P<group_name>.+)/removemember$', views.remove_member, name='removemember'),
    url(r'^group/(?P<group_name>.+)/addfile$', views.add_file, name='addfile'),
    url(r'^group/(?P<group_name>.+)/removefile$', views.remove_file, name='removefile'),
    url(r'^group/(?P<group_name>.+)/sendgroupinvite$', views.send_group_invite, name='sendgroupinvite'),
    url(r'^group/(?P<group_name>.+)/leavegroup$', views.leave_group, name='leavegroup'),
    url(r'^group/(?P<group_name>.+)/deletegroup$', views.delete_group, name='deletegroup'),
    url(r'^creategroup/$', views.create_group, name='create_group'),
    url(r'^invites/$', views.invites, name='invites'),
    url(r'^answerinvite/(?P<group_id>[0-9]+)/$', views.answer_invite, name='answerinvite'),
    url(r'^savegroup/$', views.save_group, name='savegroup'),
    url(r'^premium/$', views.premium, name='premium'),
    url(r'^gopremium/$', views.go_premium, name='gopremium'),
    url(r'^gonormal/$', views.go_normal, name='gonormal'),
]
