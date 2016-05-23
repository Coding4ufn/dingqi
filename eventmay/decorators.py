# Created by TTc9082 on 5/13/16
# coding: utf-8
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
import re


def wechat_only(function=None):
    """如果是手机中，只允许微信的页面。其它浏览器返回二维码。"""

    def do_filter_browser(func):
        def __filter_browser(request, *args, **kwargs):
            # if request.META.get('HTTP_HOST') == settings.MOBILE_SITE:
            wechat_browser = True if re.search('MicroMessenger', request.META.get('HTTP_USER_AGENT', '')) else False
            if not wechat_browser:
                return redirect(reverse('wechat qr') + '?next=' + settings.WEB_SITE_ROOT + request.path)
            return func(request, *args, **kwargs)

        return __filter_browser

    if function:
        return do_filter_browser(function)
    return do_filter_browser


def wechat_auth_open(function=None):
    """手机地址转微信授权地址。"""
    def do_filter_browser(func):
        def __filter_browser(request, *args, **kwargs):
            if request.META.get('HTTP_HOST') == settings.MOBILE_SITE:
                wechat_browser = True if re.search('MicroMessenger', request.META.get('HTTP_USER_AGENT', '')) else False
                if not wechat_browser:
                    return redirect(
                        reverse('wechat qr') + '?next=https://open.weixin.qq.com/connect/oauth2/authorize?appid='
                        + settings.WECHAT_ID + '&redirect_uri='
                        + 'http://' + settings.MOBILE_SITE + request.path + '?showwxpaytitle=1'
                        + '&response_type=code&scope=snsapi_userinfo&state=123#wechat_redirect'
                    )
                elif not request.GET.get('code', None):
                    return redirect(
                        'https://open.weixin.qq.com/connect/oauth2/authorize?appid='
                        + settings.WECHAT_ID + '&redirect_uri='
                        + 'http://' + settings.MOBILE_SITE + request.path + '?showwxpaytitle=1'
                        + '&response_type=code&scope=snsapi_userinfo&state=123#wechat_redirect'
                    )
            return func(request, *args, **kwargs)

        return __filter_browser

    if function:
        return do_filter_browser(function)
    return do_filter_browser