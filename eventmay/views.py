# coding: utf-8
from django.shortcuts import render, get_object_or_404
from wechat.models import *
from decorators import *
from wechat.utils import *


@wechat_only
@wechat_auth_open
def user_page(request, fakeid):
    """个人页面"""
    code = request.GET.get('code', '')
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    unionid = info['unionid']
    wechat_user = WechatUser.objects.get_or_create(unionid=unionid)
    WechatUser.objects.filter(id=wechat_user.id).update(**info)
    context = {}
    context.update(prepare_wechat(request.build_absolute_uri()))
    return render(request, '', context)


def rank(request):
    """排名页面"""
    context = {}
    return render(request, '', context)