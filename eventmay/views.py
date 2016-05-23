# coding: utf-8
from cStringIO import StringIO
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from wechat.models import *
from decorators import *
from models import *
from wechat.utils import *
import base64
import qrcode


@wechat_only
@wechat_auth_open
def user_page(request, fakeid):
    """个人页面"""
    current_user = get_object_or_404(WechatUser, unionid=fakeid)
    code = request.GET.get('code', '')
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    openid = info['openid']
    wechat_user, created = WechatUser.objects.get_or_create(openid=openid)
    map(lambda x: info.pop(x), ['subscribe_time', 'remark', 'groupid', 'subscribe', 'language', 'tagid_list'])
    WechatUser.objects.filter(id=wechat_user.id).update(**info)
    context = {'user': wechat_user, 'current_user': current_user}
    context.update(prepare_wechat(request.build_absolute_uri()))
    return render(request, 'user_page.html', context)


def add(request, helped_id, helper_id):
    current_user = WechatUser.objects.get(unionid=helped_id)
    unionid = helper_id
    helper = WechatUser.objects.get(unionid=unionid)
    if not helper or not current_user:
        score = ''
        created = ''
        name = ''
        avatar = ''
        error = 1
    else:
        name = helper.nickname
        avatar = helper.headimgurl
        add_score, created = AddScore.objects.get_or_create(user=current_user, helper=helper)
        error = 0
        score = add_score.score
    context = {'score': score, 'created': created, 'error': error, 'name': name, 'avatar': avatar}
    return JsonResponse(context)


@wechat_only
def join(request, openid):
    wechat = WechatMPAuth()
    info = wechat.get_mp_user_info(openid)
    map(lambda x: info.pop(x), ['subscribe_time', 'remark', 'groupid', 'subscribe', 'language', 'tagid_list'])
    wechat_user, created = WechatUser.objects.get_or_create(openid=openid)
    if wechat_user.score == 0:
        score = random.randint(500, 1000)
        info.update(score=score)
    WechatUser.objects.filter(id=wechat_user.id).update(**info)
    context = {'user': wechat_user}
    context.update(prepare_wechat(request.build_absolute_uri()))
    return render(request, 'user_page.html', context)


def rank(request):
    """排名页面"""
    context = {}
    return render(request, '', context)


def wechat_qr(request):
    current_url = request.GET.get('next', '')
    img = qrcode.make(current_url)
    output = StringIO()
    img.save(output)
    output.seek(0)
    output_s = output.read()
    b64 = base64.b64encode(output_s)
    context = {'qr': b64}
    return render(request, 'wechat_qr.html', context)