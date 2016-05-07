# coding: utf-8

from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils import timezone


class WechatSettings(models.Model):
    """微信公众平台相关设置"""
    key = models.CharField(u'配置名称', max_length=512)
    expires = models.DateTimeField(u'过期时间', blank=True, null=True)
    updated = models.DateTimeField(u'更新时间', auto_now=True)
    value = models.CharField(u'配置名称', max_length=1024, blank=True, null=True)

    def __unicode__(self):
        return self.key + ': ' + self.value


class WechatAccessToken(models.Model):
    access_token = models.CharField(u'access token', max_length=512)
    token_expire_at = models.DateTimeField(u'token expire time', )
    token_requested_at = models.DateTimeField(u'token request time', auto_now=True)

    def __unicode__(self):
        return self.token_requested_at


class WechatTicket(models.Model):
    jsapi_ticket = models.CharField(u'jsapi ticket', max_length=512)
    ticket_expire_at = models.DateTimeField(u'ticket expire time', )
    ticket_requested_at = models.DateTimeField(u'ticket request time', auto_now=True)

    def __unicode__(self):
        return self.ticket_requested_at


MESSAGE_TYPES = (
    ('unknown', u'未知事件'),
    ('event', u'普通事件'),
    ('scancode_push', u'扫码推送事件'),
    ('text', u'文字消息'),
    ('image', u'图片消息'),
    ('voice', u'语音消息'),
    ('video', u'视频消息'),
    ('shortvideo', u'小视频消息'),
    ('location', u'地理位置消息'),
)

EVENT_TYPES = (
    ('unknown', u'未知事件'),
    ('CLICK', u'点击菜单拉取消息'),
    ('SCAN', u'扫码事件'),
    ('subscribe', u'订阅'),
    ('unsubscribe', u'取消订阅'),
    ('VIEW', u'点击菜单跳转链接'),
)


class WechatMessage(models.Model):
    """微信消息接收历史记录"""
    to_user_name = models.CharField(u'收取人', max_length=64)
    from_user_name = models.CharField(u'发送人', max_length=64)
    create_time = models.DateTimeField(u'发送时间', default=None, null=True)
    msg_type = models.CharField(u'消息类型', max_length=32, default='unknown', choices=MESSAGE_TYPES, null=True, blank=True)
    content = models.CharField(u'消息内容', max_length=512, null=True, blank=True)
    msg_id = models.CharField(u'消息id', max_length=64, null=True, blank=True)
    event = models.CharField(u'事件内容', max_length=32, default='unknown', choices=EVENT_TYPES, null=True, blank=True)
    event_key = models.CharField(u'事件key', max_length=512, null=True, blank=True)
    scan_type = models.CharField(u'扫描类型', max_length=32, null=True, blank=True)
    scan_result = models.CharField(u'扫描结果', max_length=256, null=True, blank=True)

    def __unicode__(self):
        return self.msg_id + str(self.create_time)


class WechatUser(models.Model):
    """微信用户信息及关系"""
    access_token = models.CharField(u'access_token', max_length=256, default=u'')
    refresh_token = models.CharField(u'refresh_token', max_length=256, default=u'')
    expired = models.DateTimeField(u'过期时间', default=timezone.now)
    openid = models.CharField(u'公众号获得微信open_id', max_length=64, blank=True, null=True)
    web_openid = models.CharField(u'网页扫描获得微信open_id', max_length=64, blank=True, null=True)
    user = models.OneToOneField(User, related_name='wechat', blank=True, null=True)
    created = models.DateTimeField(u'绑定时间', auto_now_add=True)
    nickname = models.CharField(u'微信名称', max_length=256, blank=True, null=True)
    headimgurl = models.CharField(u'头像地址', max_length=1024, blank=True, null=True)
    sex = models.CharField(u'性别', max_length=2, choices=((u'0', u'未知'), (u'1', u'男'), (u'2', u'女')), default=u'0')
    country = models.CharField(u'国家', max_length=256, blank=True, null=True)
    province = models.CharField(u'省', max_length=256, blank=True, null=True)
    city = models.CharField(u'市', max_length=256, blank=True, null=True)
    privilege = models.CharField(u'特权', max_length=256, blank=True, null=True)
    unionid = models.CharField(u'用户独立id', max_length=256)

    def __unicode__(self):
        return "%s" % self.nickname

    def send_notification(self, template, url, data, wechat):
        template_id = settings.MESSAGE_TEMPLATE[template]
        if self.openid:
            res = wechat.send_template_message(template_id, url, data, self.openid)
        else:
            res = {"errcode": 1, "errmsg": "openid error"}
        return res
