# coding: utf-8

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from settings import *
from xml.etree import ElementTree as ET
from wechat.models import *
from wechat.wechatauth import WechatMPAuth
from wechat.utils import parse_xml, prepare_wechat
from wechat_encrypt.WXBizMsgCrypt import WXBizMsgCrypt
from eventmay.utils import get_logger
import hashlib
from django.utils.decorators import method_decorator
from django.views.generic import View


class WechatInterface(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        处理基础参数, 根据方法分配到各自的Method中
        """
        self.nonce = request.GET.get('nonce', None)
        self.timestamp = request.GET.get('timestamp', None)
        self.signature = request.GET.get('signature', None)
        self.token = TOKEN
        return super(WechatInterface, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        """
        GET方法访问接口的处理, 仅仅用于微信接口验证
        """
        echostr = request.GET.get('echostr', None)
        hashed_text = hashlib.sha1(''.join(sorted([self.token, self.timestamp, self.nonce]))).hexdigest()
        if hashed_text == self.signature:
            return HttpResponse(echostr)
        else:
            return HttpResponse('error')

    def post(self, request):
        """
        POST方法访问接口的处理, 用于处理微信交互信息
        :param request:
        """
        logger = get_logger(__name__)
        # Parsing encrypted XML CDATA
        raw_str = smart_str(request.body)
        msg_signature = request.GET.get('msg_signature', None)
        logger.info(msg_signature)
        logger.info(raw_str)
        # Decrypt messages using AES
        crypt = WXBizMsgCrypt(self.token, encodingAESKey, WECHAT_ID)
        logger.info(crypt)
        ret, _xml = crypt.DecryptMsg(raw_str, msg_signature, self.timestamp, self.nonce)
        logger.info(_xml)
        logger.info(ret)
        # Parsing clear text XML CDATA
        msg = parse_xml(ET.fromstring(_xml))
        # Store messages in database
        self.create_time_ts = msg.get('CreateTime')
        create_time = timezone.datetime.fromtimestamp(float(self.create_time_ts))
        user_msg = {'to_user_name': msg.get('ToUserName', None),
                    'from_user_name': msg.get('FromUserName', None),
                    'create_time': create_time,
                    'msg_type': msg.get('MsgType', None),
                    'content': msg.get('Content', None),
                    'msg_id': msg.get('MsgId', None),
                    'event': msg.get('Event', None),
                    'event_key': msg.get('EventKey', None),
                    'scan_type': msg.get('ScanType', None),
                    'scan_result': msg.get('ScanResult', None)}
        wechat_message = WechatMessage(**user_msg)
        wechat_message.save()
        if wechat_message.msg_type == 'event':
            return self.event_handler(request, wechat_message=wechat_message)
        elif wechat_message.msg_type == 'text':
            return self.text_handler(request, wechat_message=wechat_message)

    def event_handler(self, request, wechat_message=None):
        """
        微信事件处理: 分配允许的event到各自的method中处理
        :param wechat_message:
        :param request:
        """
        if wechat_message.event in ['SCAN', 'subscribe', 'CLICK', 'VIEW', 'unsubscribe', 'TEMPLATESENDJOBFINISH',
                                    'kf_create_session', 'kf_close_session']:
            handler = getattr(self, wechat_message.event.lower())
        else:
            handler = self.http_method_not_allowed
        return handler(request, wechat_message)

    def subscribe(self, request, wechat_message):
        """
        处理关注事件
        :param wechat_message:
        :param request:
        """
        context = {}
        wechat_mp = WechatMPAuth()
        user_info = wechat_mp.get_mp_user_info(wechat_message.from_user_name)
        wechat_user, created = WechatUser.objects.get_or_create(unionid=user_info['unionid'])
        return render(request, 'text_reply.xml', context)

    def unsubscribe(self, request, wechat_message):
        """
        取关时删除微信关联用户
        """
        WechatUser.objects.filter(openid=wechat_message.from_user_name).update(openid=None)
        return HttpResponse('success')

    def templatesendjobfinish(self, request, wechat_message):
        return

    def scan(self, request, wechat_message):
        """
        处理扫描事件
        """
        context = {}
        return render(request, 'text_reply.xml', context)

    def click(self, request, wechat_message):
        logger = get_logger(__name__)
        context = {}
        logger.info('clicking')
        if wechat_message.event_key == 'join':
            logger.info('joining')
            items = [
                {'title': u'顶奇夏日狂欢节',
                 'description': u'土豪带你玩迪士尼，住裸心谷！！！玩住都免费！！！邀请朋友玩游戏，赢好礼。',
                 'get_absolute_pic_url': 'https://mmbiz.qlogo.cn/mmbiz/dBFTVtHX0pLQfibUF5PEgBoVpyOibp86N94BhzeKP7MfaoCRnaQvWBefy2sAUX40QExQNsib8auTv2XeFUjR9BIxA/0?wx_fmt=jpeg',
                 'url': 'http://mp.weixin.qq.com/s?__biz=MzI5MjEzNjAxNA==&mid=502018828&idx=1&sn=324270690f6b30d5c80198de1702b346#rd'},
                {'title': u'点此立即参与攒顶奇洗衣液游戏',
                 'description': '',
                 'get_absolute_pic_url': '',
                 'url': settings.WEB_SITE_ROOT + reverse('join', args=[wechat_message.from_user_name])},
                {'title': u'查看游戏排行榜',
                 'description': '',
                 'get_absolute_pic_url': '',
                 'url': settings.WEB_SITE_ROOT + reverse('rank')}
            ]
            context = {'to_user': wechat_message.from_user_name,
                       'from_user': wechat_message.to_user_name,
                       'create_time': self.create_time_ts,
                       'items': items,
                       'len': len(items)}
            from django.template import loader
            logger.info(loader.render_to_string('news.xml', context))
            return render(request, 'news.xml', context)
        elif wechat_message.event_key == 'prize':
            wechat_mp = WechatMPAuth()
            if not WechatUser.objects.filter(openid=wechat_message.from_user_name):
                reply = u'您还没参加游戏呢!'
            else:
                prize = Prize.objects.get(user__openid=wechat_message.from_user_name)
                your_score = WechatUser.objects.filter(openid=wechat_message.from_user_name).first().score
                your_rank = WechatUser.objects.filter(score__gt=your_score).count() + 1
                if prize:
                    reply = u'恭喜你, 你攒到了顶奇洗衣液%sml, 目前的排名为%s。获得奖品顶奇洗衣液一瓶。复制这条信息，打开手机淘宝即可看到 ￥AAFLCOXS￥http://tmqd.me/h.Fj7uj?cv=AAFLCOXS, 下单并备注兑换码%s' % (your_score, your_rank, prize.code)
                else:
                    reply = u'你攒到了顶奇洗衣液%sml, 目前的排名为%s。还不能领取奖品哦, 快去寻找小伙伴的帮助吧!' % (your_score, your_rank)
            context = {"to_user": wechat_message.from_user_name, "from_user": wechat_message.to_user_name,
                       "create_time": self.create_time_ts, "reply": reply}
            return render(request, 'text_reply.xml', context)

    def kf_create_session(self, request, wechat_message):
        """
        客服进程开始
        """
        wechat_mp = WechatMPAuth()
        wechat_mp.send_customer_service_text(wechat_message.from_user_name, '客服已接入。')
        return HttpResponse('')

    def kf_close_session(self, request, wechat_message):
        """
        客服断开
        """
        wechat_mp = WechatMPAuth()
        wechat_mp.send_customer_service_text(wechat_message.from_user_name, '已与客服断开。')
        return HttpResponse('')

    def text_handler(self, request, wechat_message):
        if wechat_message.content == u'口碑街':
            reply = u'测试一下中文字符还行不行了卧槽'
            context = {"to_user": wechat_message.from_user_name, "from_user": wechat_message.to_user_name,
                       "create_time": self.create_time_ts, "reply": reply}
            return render(request, 'text_reply.xml', context)
        else:
            wechat_mp = WechatMPAuth()
            wechat_mp.send_customer_service_text(wechat_message.from_user_name, '正在为您接入客服...请稍候...')
            context = {"to_user": wechat_message.from_user_name, "from_user": wechat_message.to_user_name,
                       "create_time": self.create_time_ts}
            return render(request, 'customer_service.xml', context)