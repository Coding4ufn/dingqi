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
    current_user = get_object_or_404(WechatUser, id=fakeid)
    code = request.GET.get('code', '')
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    openid = info['openid']
    info.pop('language')
    wechat_user, created = WechatUser.objects.get_or_create(openid=openid)
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
        helping, created = Help.objects.get_or_create(helper=helper, helped=current_user)
        error = 0
        score = helping.score
    context = {'score': score, 'created': created, 'error': error, 'name': name, 'avatar': avatar}
    return JsonResponse(context)



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