# coding: utf-8
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import smart_str
from wechat.wechatauth import WechatMPAuth
from wechat.models import WechatSettings
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


def wx_get_read_num_by_url(url):
    """
    公众文章阅读数读取
    url : 微信公众文章url地址
    返回:
    阅读数, 点赞数
    """
    uin = WechatSettings.objects.get(key='wechat_uin').value
    key = WechatSettings.objects.get(key='wechat_key').value
    result = urlparse.urlparse(url)
    res_values = urlparse.parse_qs(result.query, True)
    biz = res_values['__biz'][0]
    mid = res_values['mid'][0]
    sn = res_values['sn'][0]
    idx = res_values['idx'][0]
    base_url = 'http://mp.weixin.qq.com/mp/getappmsgext'
    para = {
        'key': key,
        '__biz': biz,
        'mid': mid,
        'sn': sn,
        'idx': idx,
        'uin': uin,
    }
    headers = {
        'User-Agent': 'MQQBrowser/5.4 TBS/025483 Mobile Safari/533.1 MicroMessenger/6.3.8.56_re6b2553.680 NetType/WIFI Language/zh_CN'
    }
    res = requests.post(base_url, headers=headers, params=para, data={'is_only_read': 1})
    print res.json()
    try:
        read = res.json()['appmsgstat']['real_read_num']
        if read == 0:
            read = res.json()['appmsgstat']['read_num']
        like = res.json()['appmsgstat']['like_num']
    except KeyError:
        raise Exception(u'read_num empty %s' %  res.json())
    return read, like