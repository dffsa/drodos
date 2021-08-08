from django.db import models

# Create your models here.
import datetime
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, null=True)
    premium = models.BooleanField(default=False)
    maxStorage = models.IntegerField(default=10000)
    currentStorage = models.IntegerField(default=0)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return 'Username: ' + self.user.username + ' Email: ' + self.user.email


class StoredItem(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    fileUrl = models.CharField(max_length=100, null=True)
    private = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def sharedwith(self, user):
        groups = Group.objects.filter(member=user)
        for group in groups:
            if group.hasitem(self):
                return True
        return False


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    member = models.ManyToManyField(User, related_name='member')
    item = models.ManyToManyField(StoredItem, related_name='item')
    name = models.CharField(max_length=50, default=None, blank=True)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

    def ismember(self, user):
        return user in self.member.all()

    def isowner(self, user):
        return user == self.owner

    def hasitem(self, item):
        return item in self.item.all()


class Invite(models.Model):
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitee')
    invited = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited')
    toGroup = models.ForeignKey(Group, on_delete=models.CASCADE)


class Comment(models.Model):
    StoredItem = models.ForeignKey(StoredItem, on_delete=models.CASCADE)
    text = models.TextField();
    pub_date = models.DateField('data de publicacao')