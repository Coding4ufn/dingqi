# coding:utf-8

from django.db import models
from wechat.models import *
from utils import get_score

# Create your models here.


class Help(models.Model):
    created = models.DateTimeField(u'帮助时间', auto_now_add=True)
    helper = models.ForeignKey(WechatUser, related_name='helped')
    helped = models.ForeignKey(WechatUser, related_name='helped_by')
    score = models.IntegerField(u'帮助数值', default=get_score)
