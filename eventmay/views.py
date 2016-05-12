# coding: utf-8
from cStringIO import StringIO
from django.shortcuts import render, get_object_or_404
from wechat.models import *
from decorators import *
from wechat.utils import *
import base64
import qrcode


@wechat_only
@wechat_auth_open
def user_page(request, fakeid):
    """个人页面"""
    code = request.GET.get('code', '')
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    openid = info['openid']
    wechat_user, created = WechatUser.objects.get_or_create(openid=openid)
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