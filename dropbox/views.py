from django.shortcuts import render, redirect

# Create your views here.
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .models import *
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as d_login, logout as d_logout
from django.core.files.storage import FileSystemStorage
from .forms import RegisterForm, GroupForm


def index(request):
    print(User.objects.all())
    print('currently logged in as :' + request.user.username)
    return render(request, 'home.html')


def register(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return render(request, 'home.html')
        else:
            form = RegisterForm()
            return render(request, 'register.html', {'form': form})
    elif request.method == 'POST':
        form = RegisterForm(request.POST)
        if not (User.objects.filter(username=request.POST['username']).exists() or User.objects.filter(
                email=request.POST['email']).exists()):
            if form.is_valid():
                user = User.objects.create_user(request.POST['username'], request.POST['email'],
                                                request.POST['password'])
                user.profile.bio = request.POST['biography']
                user.save()
                return render(request, 'registered.html')
            else:
                return render(request, 'registerfail.html', {'form': form})
        else:
            return render(request, 'registerfail.html', {'form': form})


def login(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return render(request, 'home.html', {'user': request.user})
        else:
            return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            d_login(request, user)
            return HttpResponseRedirect(reverse('dropbox:my_profile'))
        else:
            return HttpResponseRedirect(reverse('dropbox:login'))
    else:
        return render(reverse('dropbox:index'))


def logout(request):
    d_logout(request)
    return HttpResponseRedirect(reverse('dropbox:index'))


def my_profile(request):
    if request.user.is_authenticated:
        return render(request, 'myprofile.html', {'user': request.user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def upload(request):
    if request.method == 'POST':
        if not request.FILES:
            return render(request, 'home.html', {'error_message': 'no file selected'})
        else:
            files = request.FILES.getlist('filesInputId')
            fs = FileSystemStorage()
            if request.user.is_authenticated:
                for f in files:
                    filename = fs.save(fs.get_available_name(f.name), f)
                    size = fs.size(filename)/1000000 # convert to Mb
                    if request.user.profile.currentStorage + size > request.user.profile.maxStorage:
                        fs.delete(filename)
                        # return render(request, 'home.html',
                        # {'error_message': 'you don\'t have sufficient storage capacity'})
                        return HttpResponseRedirect(reverse('dropbox:index'))
                    else:
                        private = False
                        if request.POST.get('private') == 'on':
                            private = True

                        stored_item = StoredItem(owner=request.user,
                                                 fileUrl=filename, description=request.POST.get('desc', ''),
                                                 private=private)
                        request.user.profile.currentStorage += size
                        request.user.save()
                        stored_item.save()
                return HttpResponseRedirect(reverse('dropbox:files'))
            else:  # unregistered user upload
                for f in files:
                    filename = fs.save(fs.get_available_name(f.name), f)
                    size = fs.size(filename)/1000000 # convert to Mb
                    if size > 100:
                        fs.delete(filename)
                        # return render(request, 'home.html',
                        #             {'error_message': 'File too big!'}
                        return HttpResponseRedirect(reverse('dropbox:index'))
                    else:
                        temp_item = StoredItem(owner=None,
                                               fileUrl=filename, description=request.POST.get('desc', ''),
                                               private=False)
                        temp_item.save()
                return HttpResponseRedirect(reverse('dropbox:file', kwargs={'filename': filename}))


def download(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)
    if storeditem.private:
        if request.user.is_authenticated:
            if storeditem.owner == request.user or storeditem.sharedwith(request.user):  # download approved
                fb = FileSystemStorage()
                path = fb.path(filename)
                with open(path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type="application/download")
                    response['Content-Disposition'] = 'inline; filename=' + filename
                    return response
            else:  # download denied to user
                return HttpResponseRedirect(reverse('dropbox:index'))
        else:  # no download to anon
            return HttpResponseRedirect(reverse('dropbox:index'))
    else:  # public to download
        fb = FileSystemStorage()
        path = fb.path(filename)
        with open(path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/download")
            response['Content-Disposition'] = 'inline; filename=' + filename
            return response


def files(request):
    if request.user.is_authenticated:
        return render(request, 'files.html', {'files': StoredItem.objects.filter(owner=request.user)})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def file(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)

    if request.user.is_authenticated:
        if storeditem.owner == request.user:
            return render(request, 'file.html', {'storeditem': storeditem})
        else:
            if not storeditem.private or storeditem.sharedwith(request.user):
                if request.user.is_authenticated:
                    return render(request, 'viewfile2.html', {'storeditem': storeditem})
            else:
                return HttpResponseRedirect(reverse('dropbox:index'))
    else:
        if storeditem.private:
            return HttpResponseRedirect(reverse('dropbox:index'))
        else:
            return render(request, 'viewfile.html', {'storeditem': storeditem})


def groups(request):
    if request.user.is_authenticated:
        return render(request, 'groups.html',
                      {'groups': Group.objects.filter(member=request.user), 'user': request.user})
    else:
        return render(request, 'home.html')


def group(request, group_name):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, name=group_name)
        if group.ismember(request.user):
            user_items = StoredItem.objects.filter(owner=request.user)
            if group.isowner(request.user):  # display group owner template
                return render(request, 'group_owner.html', {'group': group, 'user_items': user_items})
            else:  # display group member template
                return render(request, 'group_member.html', {'group': group, 'user_items': user_items})
        else:  # not a member
            # display group profile to the invitee
            group = get_object_or_404(Group, name=group_name)
            return render(request, 'view_group.html', {'group': group})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def create_group(request):
    if request.user.is_authenticated and request.user.profile.premium:
        form = GroupForm()
        return render(request, 'create_group.html', {'form': form})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def invites(request):
    if request.user.is_authenticated:
        return render(request, 'invites.html', {'invites': Invite.objects.filter(invited=request.user)})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def group_invite_member(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.user.is_authenticated and group.isowner(request.user):
        return render(request, 'group_owner.html', {'inviteform': True, 'group': group})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def add_file(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.method == 'GET':
        if request.user.is_authenticated and group.ismember(request.user):
            user_items = StoredItem.objects.filter(owner=request.user)
            if group.isowner(request.user):
                return render(request, 'group_owner.html', {'addfileform': True, 'group': group,
                                                            'useritems': user_items})
            else:
                return render(request, 'group_member.html', {'addfileform': True, 'group': group,
                                                             'useritems': user_items})
        else:
            return HttpResponseRedirect(reverse('dropbox:index'))
    elif request.method == 'POST':
        if request.user.is_authenticated and group.ismember(request.user) and request.POST.get('storeditem'):
            item = StoredItem.objects.get(pk=request.POST['storeditem'])
            if not group.hasitem(item):
                group.item.add(item)
                group.save()
                return HttpResponseRedirect(reverse('dropbox:group', args=(group_name,)))
            else:
                useritems = StoredItem.objects.filter(owner=request.user)
                if group.isowner(request.user):
                    return render(request, 'group_owner.html', {'addfileform': True, 'group': group,
                                                                'useritems': useritems,
                                                                'error_message': 'File is already added in the group!'})
                else:
                    return render(request, 'group_member.html', {'addfileform': True, 'group': group,
                                                                 'useritems': useritems,
                                                                 'error_message': 'File is already added in the group!'})
    return HttpResponseRedirect(reverse('dropbox:index'))


def remove_file(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.method == 'GET':
        if request.user.is_authenticated and group.ismember(request.user):
            group_files = group.item.all()
            print(group_files)
            if group.isowner(request.user):
                return render(request, 'group_owner.html', {'removefileform': True, 'group': group,
                                                            'usergroupitems': group_files})
            else:
                usergroupitems = []
                for storeditem in group_files:
                    if group.hasitem(storeditem):
                        usergroupitems.append(storeditem)
                return render(request, 'group_member.html', {'removefileform': True, 'group': group,
                                                             'usergroupitems': usergroupitems})
        else:
            return HttpResponseRedirect(reverse('dropbox:index'))
    elif request.method == 'POST':
        if request.user.is_authenticated and group.ismember(request.user) and request.POST.get('storeditem'):
            item = StoredItem.objects.get(fileUrl=request.POST['storeditem'])
            if group.hasitem(item) and (item.owner == request.user or group.isowner(request.user)):
                group.item.remove(item)
                group.save()
                return HttpResponseRedirect(reverse('dropbox:group', args=(group_name,)))
            else:  # user is a member but is trying to remove a file of another member
                return HttpResponseRedirect(reverse('dropbox:group', args=(group_name,)))
    return HttpResponseRedirect(reverse('dropbox:index'))


def delete_file(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)
    if request.user == storeditem.owner:
        storeditem.delete()
        fs = FileSystemStorage()
        size = int(fs.size(filename) / 1000000)
        print(size)
        request.user.profile.currentStorage -= size
        request.user.save()
        fs.delete(filename)
        return HttpResponseRedirect(reverse('dropbox:files'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def change_settings(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)
    if request.user == storeditem.owner and request.user.profile.premium:
        if storeditem.private:
            storeditem.private = False
            storeditem.save()
            return render(request, 'file.html', {'changed': 'public', 'storeditem': storeditem})
        else:
            storeditem.private = True
            storeditem.save()
            return render(request, 'file.html', {'changed': 'private', 'storeditem': storeditem})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def leave_group(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.user.is_authenticated and group.ismember(request.user):
        group.member.remove(request.user)
        print('left group')
        return HttpResponseRedirect(reverse('dropbox:groups'))
    else:  # impossible
        return HttpResponseRedirect(reverse('dropbox:index'))


def delete_group(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.user.is_authenticated and group.isowner(request.user):
        group.delete()
        print('group deleted')
        return HttpResponseRedirect(reverse('dropbox:groups'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def remove_member(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.method == 'GET':
        if request.user.is_authenticated and group.isowner(request.user):
            return render(request, 'group_owner.html', {'removeform': True, 'group': group})
        else:
            return HttpResponseRedirect(reverse('dropbox:index'))
    elif request.method == 'POST':
        if request.user.is_authenticated and group.isowner(request.user) and request.POST.get('user'):
            user_to_remove = User.objects.get(pk=request.POST['user'])
            if user_to_remove != group.owner and group.ismember(user_to_remove):
                group.member.remove(user_to_remove)
                group.save()
                return HttpResponseRedirect(reverse('dropbox:group', args=(group_name,)))
    return HttpResponseRedirect(reverse('dropbox:index'))


def send_group_invite(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if request.user.is_authenticated and group.isowner(request.user):
        if User.objects.filter(username=request.POST['username']).exists():
            invited = get_object_or_404(User, username=request.POST['username'])
            if group.ismember(invited):
                # invited is already a member
                return render(request, 'group_owner.html',
                              {'group': group, 'error_message': 'User is already a member!', 'inviteform': True})
            elif Invite.objects.filter(invitee=request.user, invited=invited, toGroup=group).exists():
                # invited is already invited
                return render(request, 'group_owner.html',
                              {'group': group, 'error_message': 'User is already invited!', 'inviteform': True})
            else:
                invite = Invite.objects.create(invitee=request.user, invited=invited, toGroup=group)
                invite.save()
                print('invite sent')
                return HttpResponseRedirect(reverse('dropbox:group', args=(group_name,)))
        else:
            return render(request, 'group_owner.html',
                          {'group': group, 'error_message': 'No user found!', 'inviteform': True})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def answer_invite(request, group_id):
    if request.user.is_authenticated:
        invite = Invite.objects.get(id=group_id)
        if request.POST['op'] == 'Accept':
            invite.toGroup.member.add(invite.invited)
            invite.toGroup.save()
            Invite.objects.get(id=invite.id).delete()
            return HttpResponseRedirect(reverse('dropbox:groups'))
        elif request.POST['op'] == 'Decline':
            Invite.objects.get(id=invite.id).delete()
            return HttpResponseRedirect(reverse('dropbox:groups'))
        else:  # invalid op
            return HttpResponseRedirect(reverse('dropbox:managegroups'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def save_group(request):
    if not Group.objects.filter(name=request.POST['name']).exists():
        form = GroupForm(request.POST)
        if form.is_valid():
            group = Group.objects.create(owner=request.user, name=request.POST['name'],
                                         description=request.POST['description'])
            group.member.add(request.user)
            group.save()
            return HttpResponseRedirect(reverse('dropbox:groups'))
        else:
            print(form.errors)
            return render(request, 'create_group.html', {'form': form, 'error_message': 'Group name already taken!'})
    else:
        form = GroupForm()
        return render(request, 'create_group.html', {'form': form, 'error_message': 'Group name already taken!'})


def user(request, username):
    if request.user.is_authenticated:
        if request.user.username == username:
            return HttpResponseRedirect(reverse('dropbox:my_profile'))
        else:
            user = get_object_or_404(User, username=username)
            return render(request, 'user.html', {'user': user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def premium(request):
    if request.user.is_authenticated:
        return render(request, 'premium.html', {'user': user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def go_premium(request):
    if request.user.is_authenticated:
        request.user.profile.premium = True
        request.user.profile.maxStorage = 1000000000
        request.user.save()
        return HttpResponseRedirect(reverse('dropbox:my_profile'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def go_normal(request):
    if request.user.is_authenticated:
        request.user.profile.premium = False
        request.user.profile.maxStorage = 10000000
        request.user.save()
        return HttpResponseRedirect(reverse('dropbox:my_profile'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))
