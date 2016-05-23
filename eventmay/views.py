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
def user_page(request, openid):
    """个人页面"""
    current_user = get_object_or_404(WechatUser, openid=openid)
    code = request.GET.get('code', '')
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    c_openid = info['openid']
    wechat_user, created = WechatUser.objects.get_or_create(openid=c_openid)
    map(lambda x: info.pop(x), ['subscribe_time', 'remark', 'groupid', 'subscribe', 'language', 'tagid_list'])
    WechatUser.objects.filter(id=wechat_user.id).update(**info)
    context = {'user': wechat_user, 'current_user': current_user}
    context.update(prepare_wechat(request.build_absolute_uri()))
    return render(request, 'user_page.html', context)


def add(request, helped_id, helper_id):
    user = WechatUser.objects.get(openid=helped_id)
    helper = WechatUser.objects.get(openid=helper_id)
    if not helper or not user:
        score = ''
        created = ''
        name = ''
        avatar = ''
        error = 2
    elif helper == user:
        score = ''
        created = ''
        name = ''
        avatar = ''
        error = 1
    else:
        name = helper.nickname
        avatar = helper.headimgurl
        add_score, created = AddScore.objects.get_or_create(user=user, helper=helper)
        error = 0
        score = add_score.score
        user.score += score
        user.save()
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
        AddScore.objects.create(user=wechat_user, helper=wechat_user, score=score)
    WechatUser.objects.filter(id=wechat_user.id).update(**info)
    wechat_user = WechatUser.objects.get(id=wechat_user.id)
    url = settings.WEB_SITE_ROOT + reverse('user page', args=[wechat_user.openid])
    context = {'user': wechat_user, 'current_user': wechat_user, 'addscores': wechat_user.addscore_set.all(), 'url': url}
    context.update(prepare_wechat(request.build_absolute_uri()))
    return render(request, 'user_page.html', context)


def rank(request):
    """排名页面"""
    ranked_users = WechatUser.objects.all().order_by('-score')[:50]
    context={'ranked_users': ranked_users}
    return render(request, 'rank.html', context)


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