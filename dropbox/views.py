from django.shortcuts import render

# Create your views here.
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .models import *
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from .forms import RegisterForm, GroupForm


def index(request):
    print(User.objects.all())
    print('currently logged in as :' + request.user.username)
    if request.user.is_authenticated:
        files = StoredItem.objects.filter(owner=request.user)
        return render(request, 'home.html', {'files': files, 'user': request.user})
    else:
        return render(request, 'index.html')


def loginp(request):
    if request.user.is_authenticated:
        return render(request, 'home.html', {'user': request.user})
    else:
        return render(request, 'login.html')


def logoutp(request):
    logout(request)
    return render(request, 'index.html')
    HttpResponseRedirect(reverse('dropbox:index'))


def register(request):
    if request.user.is_authenticated:
        return render(request, 'home.html', {'user': request.user})
    else:
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})


def checklogin(request):
    username = request.POST['username']
    password = request.POST['password']
    # check for password
    user = authenticate(username=username, password=password)
    if user is not None:
        # valid login
        login(request, user)
        #print(request.user.profile.bio)
        return HttpResponseRedirect(reverse('dropbox:index'))
    else:
        # invalid login
        return HttpResponseRedirect(reverse('dropbox:loginp'))


def checkregister(request):
    if not (User.objects.filter(username=request.POST['username']).exists() or User.objects.filter(
            email=request.POST['email']).exists()):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
            user.profile.maxStorage = 10000
            user.profile.bio = request.POST['biography']
            user.save()
            return HttpResponseRedirect(reverse('dropbox:registered'))
        else:
            return HttpResponseRedirect(reverse('dropbox:registerfail', ))
    else:
        return HttpResponseRedirect(reverse('dropbox:registerfail', ))


def registerfail(request):
    if request.user.is_authenticated:
        return render(request, 'home.html', {'user': request.user})
    else:
        form = RegisterForm()
        return render(request, 'registerfail.html', {'form': form})


def registered(request):
    if request.user.is_authenticated:
        return render(request, 'home.html', {'user': request.user})
    else:
        return render(request, 'registered.html')


def upload(request):
    if request.method == 'POST':
        print(request.FILES)
        if not request.FILES:
            if request.user.is_authenticated:
                return render(request, 'home.html', {'erro': 'no file selected', 'user': request.user})
            else:
                return render(request, 'index.html', {'erro': 'no file selected'})
        else:
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(fs.get_available_name(file.name), file)
            size = int(fs.size(filename) / 1000)
            print(str(size) + ' kb')
            if request.user.is_authenticated:
                if request.user.profile.currentStorage + size > request.user.profile.maxStorage:  # max storage reached
                    fs.delete(filename)
                    return HttpResponseRedirect(reverse('dropbox:myprofile'))
                else:  # proceed with upload
                    if request.POST.get('private') and request.user.profile.premium:
                        storeditem = StoredItem(owner=request.user, title=request.POST['title'],
                                                fileUrl=filename, description=request.POST['desc'],
                                                private=True)
                        print('PRIVATE')
                    else:
                        storeditem = StoredItem(owner=request.user, title=request.POST['title'],
                                                fileUrl=filename, description=request.POST['desc'],
                                                private=False)
                        print('PUBLIC')
                    request.user.profile.currentStorage += size
                    request.user.save()
                    storeditem.save()
                    return HttpResponseRedirect(reverse('dropbox:files'))
            else:  # unregistered user upload
                if size > 1000:  # too big for unregistered
                    fs.delete(filename)
                    return HttpResponseRedirect(reverse('dropbox:index'))
                else:
                    tempitem = StoredItem(owner=None, title=request.POST['title'],
                                          fileUrl=filename, description=request.POST['desc'], private=False)
                    tempitem.save()
                    return HttpResponseRedirect(reverse('dropbox:uploaded', args=(filename,)))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def upload2(request):
    if request.method == 'POST':
        if not request.FILES:
            if request.user.is_authenticated:
                return render(request, 'home.html', {'erro': 'no file selected', 'user': request.user})
            else:
                return render(request, 'index.html', {'erro': 'no file selected'})
        else:
            files = request.FILES.getlist('filesInputId')
            if request.user.is_authenticated:
                for f in files:
                    if request.user.profile.currentStorage + f.size/1000 > request.user.profile.maxStorage:
                        return HttpResponseRedirect(reverse('dropbox:myprofile'))
                    else:
                        fs = FileSystemStorage()
                        filename = fs.save(fs.get_available_name(f.name), f)
                        size = int(fs.size(filename) / 1000)
                        print(str(size) + ' kb')
                        if request.POST.get('private') and request.user.profile.premium:
                            storeditem = StoredItem(owner=request.user, title=f.name,
                                                    fileUrl=filename, description='',
                                                    private=True)
                        else:
                            storeditem = StoredItem(owner=request.user, title=f.name,
                                                    fileUrl=filename, description='',
                                                    private=False)
                        request.user.profile.currentStorage += size
                        request.user.save()
                        storeditem.save()
                return HttpResponseRedirect(reverse('dropbox:files'))
            else:  # unregistered user upload
                for f in files:
                    if f.size < 1000000:  # too big for unregistered
                        fs = FileSystemStorage()
                        filename = fs.save(fs.get_available_name(f.name), f)
                        size = int(fs.size(filename) / 1000)
                        print(str(size) + ' kb')
                        tempitem = StoredItem(owner=None, title=f.name,
                                              fileUrl=filename, description='', private=False)
                        tempitem.save()
                        return HttpResponseRedirect(reverse('dropbox:file', args=[filename]))
                    else: HttpResponseRedirect(reverse('dropbox:index'))
            return HttpResponseRedirect(reverse('dropbox:index'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def uploaded(request, filename):
    if request.user.is_authenticated:
        return render(request, 'home.html', {'user': request.user})
    else:
        return render(request, 'uploaded.html', {'filename': filename})


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
                    print('file downloaded')
                    return response
            else:  # download denied to user
                return HttpResponseRedirect(reverse('dropbox:index'))
        else:  # no download to anon
            return HttpResponseRedirect(reverse('dropbox:index'))

    else:  # public to download
        fb = FileSystemStorage()
        path = fb.path(filename)
        print(storeditem)
        with open(path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/download")
            response['Content-Disposition'] = 'inline; filename=' + filename
            print('file downloaded')
            return response


def files(request):
    if request.user.is_authenticated:
        files = StoredItem.objects.filter(owner=request.user)
        return render(request, 'files.html', {'files': files})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def file(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)
    if request.user.is_authenticated:
        if storeditem.owner == request.user:
            return render(request, 'file.html', {'storeditem': storeditem})
        else:
            if not storeditem.private or storeditem.sharedwith(request.user):
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
        groups = Group.objects.filter(member=request.user)
        return render(request, 'groups.html', {'groups': groups, 'user': request.user})
    else:
        return render(request, 'index.html')


def group(request, groupname):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, name=groupname)
        if group.ismember(request.user):
            useritems = StoredItem.objects.filter(owner=request.user)
            if group.isowner(request.user):  # group owner
                return render(request, 'groupowner.html', {'group': group, 'useritems': useritems})
            else:  # groupmember
                return render(request, 'group.html', {'group': group, 'useritems': useritems})
        else:  # not a member
            # mostrar aqui perfil do grupo para o user que for convidado poder ver
            return HttpResponseRedirect(reverse('dropbox:index'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def viewgroup(request, groupname):
    if request.user.is_authenticated:
        group = get_object_or_404(Group, name=groupname)
        return render(request, 'viewgroup.html', {'group': group})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def managegroups(request):
    if request.user.is_authenticated:
        groups = Group.objects.filter(member=request.user)
        if request.POST['op'] == 'create':
            return HttpResponseRedirect(reverse('dropbox:creategroup'))
        elif request.POST['op'] == 'inv':
            return HttpResponseRedirect(reverse('dropbox:invites'))
        else:  # invalid op
            return HttpResponseRedirect(reverse('dropbox:groups', args=(groups,)))
    else:
        return render(request, 'index.html')


def invitemember(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.isowner(request.user):
        return render(request, 'groupowner.html', {'inviteform': True, 'group': group})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def removemember(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.isowner(request.user):
        return render(request, 'groupowner.html', {'removeform': True, 'group': group})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def addfile(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.ismember(request.user):
        useritems = StoredItem.objects.filter(owner=request.user)
        if group.isowner(request.user):
            return render(request, 'groupowner.html', {'addfileform': True, 'group': group,
                                                              'useritems': useritems})
        else:
            return render(request, 'group.html', {'addfileform': True, 'group': group,
                                                         'useritems': useritems})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def removefile(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.ismember(request.user):
        useritems = StoredItem.objects.filter(owner=request.user)
        if group.isowner(request.user):
            return render(request, 'groupowner.html', {'removefileform': True, 'group': group,
                                                              'useritems': useritems})
        else:
            usergroupitems = []
            for storeditem in useritems:
                if group.hasitem(storeditem):
                    usergroupitems.append(storeditem)
            print(usergroupitems)
            return render(request, 'group.html', {'removefileform': True, 'group': group,
                                                         'usergroupitems': usergroupitems})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def deletefile(request, filename):
    storeditem = get_object_or_404(StoredItem, fileUrl=filename)
    if request.user == storeditem.owner:
        storeditem.delete()
        fs = FileSystemStorage()
        size = int(fs.size(filename) / 1000)
        print(size)
        request.user.profile.currentStorage -= size
        request.user.save()
        fs.delete(filename)
        return HttpResponseRedirect(reverse('dropbox:files'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def changesettings(request, filename):
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


def leavegroup(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.ismember(request.user):
        group.member.remove(request.user)
        print('left group')
        return HttpResponseRedirect(reverse('dropbox:groups'))
    else:  # impossible
        return HttpResponseRedirect(reverse('dropbox:index'))


def deletegroup(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.isowner(request.user):
        group.delete()
        print('group deleted')
        return HttpResponseRedirect(reverse('dropbox:groups'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def removedmember(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.isowner(request.user):
        if not request.POST.get('user'):
            return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
        else:
            toberemoved = User.objects.get(pk=request.POST['user'])
            if toberemoved != group.owner:
                group.member.remove(toberemoved)
                group.save()
                print('user removed')
                return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
            else:
                return HttpResponseRedirect(reverse('dropbox:index'))
    return HttpResponseRedirect(reverse('dropbox:index'))


def addedfile(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.ismember(request.user):
        if not request.POST.get('storeditem'):
            return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
        else:
            item = StoredItem.objects.get(pk=request.POST['storeditem'])
            if not group.hasitem(item):
                group.item.add(item)
                group.save()
                print('file has been added')
                return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
            else:
                useritems = StoredItem.objects.filter(owner=request.user)
                if group.isowner(request.user):
                    return render(request, 'groupowner.html', {'addfileform': True, 'group': group,
                                                                      'useritems': useritems,
                                                                      'erro': 'File is already added in the group!'})
                else:
                    return render(request, 'group.html', {'addfileform': True, 'group': group,
                                                                 'useritems': useritems,
                                                                 'erro': 'File is already added in the group!'})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def removedfile(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.ismember(request.user):
        if not request.POST.get('storeditem'):
            return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
        else:
            item = StoredItem.objects.get(pk=request.POST['storeditem'])
            if group.hasitem(item):
                if item.owner == request.user or group.isowner(request.user):
                    group.item.remove(item)
                    group.save()
                    print('file has been removed')
                    return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
                else:
                    return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
            else:
                return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def sendgroupinvite(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    if request.user.is_authenticated and group.isowner(request.user):
        if User.objects.filter(username=request.POST['username']).exists():
            invited = get_object_or_404(User, username=request.POST['username'])
            if group.ismember(invited):
                # invited is already a member
                return render(request, 'groupowner.html',
                              {'group': group, 'erro': 'User is already a member!', 'inviteform': True})
            elif Invite.objects.filter(invitee=request.user, invited=invited, toGroup=group).exists():
                # invited is already invited
                return render(request, 'groupowner.html',
                              {'group': group, 'erro': 'User is already invited!', 'inviteform': True})
            else:
                invite = Invite.objects.create(invitee=request.user, invited=invited, toGroup=group)
                invite.save()
                print('invite sent')
                return HttpResponseRedirect(reverse('dropbox:group', args=(groupname,)))
        else:
            return render(request, 'groupowner.html',
                          {'group': group, 'erro': 'No user found!', 'inviteform': True})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def creategroup(request):
    if request.user.is_authenticated and request.user.profile.premium:
        form = GroupForm()
        return render(request, 'creategroup.html', {'form': form})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def invites(request):
    if request.user.is_authenticated:
        invites = Invite.objects.filter(invited=request.user)
        return render(request, 'invites.html', {'invites': invites})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def answerinvite(request, groupid):
    if request.user.is_authenticated:
        invite = Invite.objects.get(id=groupid)
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


def savegroup(request):
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
            return render(request, 'creategroup.html', {'form': form, 'erro': 'Group name already taken!'})
    else:
        form = GroupForm()
        return render(request, 'creategroup.html', {'form': form, 'erro': 'Group name already taken!'})


def user(request, username):
    if request.user.is_authenticated:
        if request.user.username == username:
            return HttpResponseRedirect(reverse('dropbox:myprofile'))
        else:
            user = get_object_or_404(User, username=username)
            return render(request, 'user.html', {'user': user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def myprofile(request):
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=request.user.username)
        return render(request, 'myprofile.html', {'user': user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def premium(request):
    if request.user.is_authenticated:
        return render(request, 'premium.html', {'user': user})
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def gopremium(request):
    if request.user.is_authenticated:
        request.user.profile.premium = True
        request.user.profile.maxStorage = 100000
        request.user.save()
        return HttpResponseRedirect(reverse('dropbox:myprofile'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))


def gonormal(request):
    if request.user.is_authenticated:
        request.user.profile.premium = False
        request.user.profile.maxStorage = 10000
        request.user.save()
        return HttpResponseRedirect(reverse('dropbox:myprofile'))
    else:
        return HttpResponseRedirect(reverse('dropbox:index'))

def testing(request):
    return render(request, 'testing.html')