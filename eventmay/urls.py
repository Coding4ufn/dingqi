"""dingqi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from eventmay import views
# from django.contrib import admin

urlpatterns = [
    url(r'^wechat_qr/$', views.wechat_qr, name='wechat qr'),
    url(r'^u/(?P<fakeid>.+?)/$', views.user_page, name='user page'),
    url(r'^u/add/(?P<helped_id>.+?)/(?P<helper_id>.+?)/$', views.add, name='add'),
    url(r'^u/join/(?P<openid>.+?)/$', views.join, name='join'),
    url(r'^rank/$', views.rank, name='rank'),
]
