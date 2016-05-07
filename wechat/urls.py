# coding: utf-8
from wechat.views import WechatInterface
from django.conf.urls import url, include

urlpatterns = [
    url(r'^$', WechatInterface.as_view()),
]