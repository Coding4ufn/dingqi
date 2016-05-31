# Created by TTc9082 on 3/9/15
# coding: utf-8

from wechat.models import *
import json
import urllib
import requests
from eventmay.utils import get_logger
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile


class WechatMPAuth(object):
    def __init__(self, app_id=settings.WECHAT_ID, secret=settings.WECHAT_SECRET, redirect_uri=None):
        """
        默认传入公众平台id和secret,
        如需使用开放平台需声明
        """
        self.appid = app_id
        self.secret = secret
        self.redirect_uri = redirect_uri

    @property
    def access_token(self):
        return self._get_access_token()

    @property
    def open_access_token(self):
        return self._get_access_token(open_auth=True)

    @property
    def js_ticket(self):
        return self._get_js_ticket()

    def _get_access_token(self, open_auth=False):
        """
        获取access_token
        open_auth参数为bool,确定是否为微信开放平台授权
        """
        key = 'open_access_token' if open_auth else 'mp_access_token'
        token = WechatSettings.objects.filter(key=key, expires__gt=timezone.datetime.now() + timezone.timedelta(
            seconds=200)).first()
        if not token:
            payload = {'grant_type': 'client_credential', 'appid': self.appid, 'secret': self.secret}
            url = 'https://api.weixin.qq.com/cgi-bin/token'
            try:
                response = requests.get(url, params=payload)
                data = response.json()
            except:
                data = {'error': 'failed to fetch %s.' % key}
            else:
                token, created = WechatSettings.objects.get_or_create(key=key)
                token.expires = timezone.datetime.now() + timezone.timedelta(seconds=data['expires_in'])
                token.value = data['access_token']
                token.save()
        return token.value

    def _get_js_ticket(self):
        """
        获取js_ticket
        """
        key = 'js_ticket'
        ticket = WechatSettings.objects.filter(key=key, expires__gt=timezone.datetime.now() + timezone.timedelta(
            seconds=200)).first()
        if not ticket:
            payload = {'type': 'jsapi', 'access_token': self.access_token}
            url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket'
            try:
                response = requests.get(url, params=payload)
                data = response.json()
            except:
                data = {'error': 'failed to fetch %s.' % key}
            else:
                ticket, create = WechatSettings.objects.get_or_create(key=key)
                ticket.expires = timezone.datetime.now() + timezone.timedelta(seconds=data['expires_in'])
                ticket.value = data['ticket']
                ticket.save()
        return ticket.value

    def _get_user_access_token(self, code):
        """
        通过code获取用户access token
        """
        logger = get_logger(__name__)
        key = 'user_info'
        payload = {'code': code, 'grant_type': 'authorization_code', 'appid': self.appid, 'secret': self.secret}
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        res = requests.get(url, params=payload)
        res.encoding = 'utf-8'
        data = res.json()
        # except:
        #     data = {'error': 'failed to fetch %s.' % key}
        if 'error' in data:
            return data
        logger.info(data)
        expires_in = data.pop('expires_in')
        data.pop('scope')
        expired = timezone.now() + timezone.timedelta(seconds=expires_in)
        data['expired'] = expired
        return data

    @staticmethod
    def _get_user_info(access_token, openid, web=False):
        """
        获取用户信息
        """
        key = 'user_info'
        payload = {'lang': 'zh_CN', 'access_token': access_token, 'openid': openid}
        url = 'https://api.weixin.qq.com/sns/userinfo'
        try:
            res = requests.get(url, params=payload)
            res.encoding = 'utf-8'
            data = res.json()
        except:
            data = {'error': 'failed to fetch %s.' % key}
        """
        {
            "subscribe": 1,
            "openid": "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",
            "nickname": "Band",
            "sex": 1,
            "language": "zh_CN",
            "city": "广州",
            "province": "广东",
            "country": "中国",
            "headimgurl": "http://wx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/0",
           "subscribe_time": 1382694957,
           "unionid": " o6_bmasdasdsad6_2sgVt7hMZOPfL"
           "remark": "",
           "groupid": 0
        }
        """
        return data

    def get_user_info(self, code, web=False):
        """获取用户信息接口
        :param web: 是否为网页授权,是则保存openid到web_openid字段
        :param code: 微信返回的临时授权码
        """
        token = self._get_user_access_token(code)
        user_info = self._get_user_info(token['access_token'], token['openid'])
        if web:
            # 如果通过网页扫描登录，那么把openid记为web_openid，因为公众号获取的用户openid和web扫描获取的openid不一
            token['web_openid'] = token.pop('openid')
            user_info.pop('openid')
        user_info.update(token)
        return user_info

    def get_mp_user_info(self, openid=''):
        """通过openid获取已经关注公众号的用户的信息,只有在用户交互时我们得到openid时才能用"""
        key = 'user_info'
        payload = {'lang': 'zh_CN', 'access_token': self.access_token, 'openid': openid}
        url = 'https://api.weixin.qq.com/cgi-bin/user/info'
        try:
            res = requests.get(url, params=payload)
            res.encoding = 'utf-8'
            data = res.json()
        except:
            data = {'error': 'failed to fetch %s.' % key}
        """
        {
            "subscribe": 1,
            "openid": "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",
            "nickname": "Band",
            "sex": 1,
            "language": "zh_CN",
            "city": "广州",
            "province": "广东",
            "country": "中国",
            "headimgurl": "http://wx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/0",
           "subscribe_time": 1382694957,
           "unionid": " o6_bmasdasdsad6_2sgVt7hMZOPfL"
           "remark": "",
           "groupid": 0
        }
        """
        return data

    def send_template_message(self, template_id, m_url, m_data, openid):
        url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=' + self.access_token
        data = {
            "touser": openid,
            "template_id": template_id,
            "data": m_data
        }
        if m_url:
            data.update({"url": m_url})
        res = requests.post(url, json=data)
        return res.json()

    def send_customer_service_img(self, openid, media_id):
        url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + self.access_token
        data = {
            "touser": openid,
            "msgtype": "image",
            "image":
            {
              "media_id": media_id
            }
        }
        res = requests.post(url, json=data)
        return res.json()

    def send_customer_service_text(self, openid, text):
        url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + self.access_token
        data = {
            "touser": openid,
            "msgtype": "text",
            "text":
            {
                "content": text
            }
        }
        json_data = json.dumps(data, ensure_ascii=False)
        res = requests.post(url, data=json_data)
        return res.json()

    def get_scene_qr_ticket(self, scene_str):
        url = 'https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token=' + self.access_token
        data = {"action_name": "QR_LIMIT_STR_SCENE", "action_info": {"scene": {"scene_str": scene_str}}}
        res = requests.post(url, json=data)
        return res.json().get('ticket', '')

    @staticmethod
    def get_qrcode_from_ticket(ticket):
        url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=' + urllib.quote(ticket)
        res = requests.get(url)
        return res

    def get_image_from_media_id(self, media_id):
        """获得指定media_id的文件"""
        url = 'https://api.weixin.qq.com/cgi-bin/material/get_material'
        payload = {'access_token': self.access_token}
        response = requests.post(url, params=payload, json={'media_id': media_id})
        return ContentFile(response.content)