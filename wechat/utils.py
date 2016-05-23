# coding: utf-8
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import smart_str
from wechat.wechatauth import WechatMPAuth
import random
import urlparse
import hashlib
import requests


def prepare_wechat(url=None, ):
    cur_url = url
    wechat = WechatMPAuth(settings.WECHAT_ID, settings.WECHAT_SECRET)
    jsapi_ticket = wechat.js_ticket
    noncestr = str(random.randint(100000, 999999))
    timestamp = int((timezone.datetime.now() - timezone.datetime(1970, 1, 1)).total_seconds())
    params = {"jsapi_ticket": jsapi_ticket, 'noncestr': noncestr, 'timestamp': timestamp, 'url': cur_url}
    clear_text = "&".join(['%s=%s' % (key, params[key]) for key in sorted(params)])
    signature = hashlib.sha1(clear_text).hexdigest()
    context = {'signature': signature, 'appid': settings.WECHAT_ID, 'noncestr': noncestr, 'timestamp': timestamp}
    return context


def parse_xml(root_ele):
    """封装parseXML"""
    msg = {}
    if root_ele.tag == 'xml':
        for child in root_ele.iter():
            msg[child.tag] = smart_str(child.text)
    return msg


def wx_decode(string):
    replace_list = {"&#39;": "'", "&quot;": '"', "&nbsp;": " ", "&gt;": ">", "&lt;": "<", "&amp;": "&"}
    for k, v in replace_list.iteritems():
        string = string.replace(k, v)
    return string


def wx_unescape_url(string):
    replace_list = {"\/": "/", "&amp;": "&"}
    #todo:处理切割问题 会把网址切错
    for k, v in replace_list.iteritems():
        string = string.replace(k, v)
    return string
