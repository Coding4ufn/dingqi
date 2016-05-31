# coding: utf-8
from cStringIO import StringIO
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
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
    wechat_user = get_object_or_404(WechatUser, openid=openid)
    code = request.GET.get('code', '')
    if not code:
        return redirect(
            reverse('wechat qr') + '?next=https://open.weixin.qq.com/connect/oauth2/authorize?appid='
            + settings.WECHAT_ID + '&redirect_uri='
            + 'http://' + settings.MOBILE_SITE + request.path + '?showwxpaytitle=1'
            + '&response_type=code&scope=snsapi_userinfo&state=123#wechat_redirect'
        )
    wechat = WechatMPAuth()
    info = wechat.get_user_info(code)
    c_openid = info['openid']
    current_user, created = WechatUser.objects.get_or_create(openid=c_openid)
    map(lambda x: info.pop(x), ['language', 'openid'])
    WechatUser.objects.filter(id=current_user.id).update(**info)
    url = settings.WEB_SITE_ROOT + reverse('user page', args=[wechat_user.openid])
    max_value = 3000
    if wechat_user.score >= 3000:
        max_value = wechat_user.score * 1.43
    context = {'user': wechat_user, 'current_user': current_user, 'addscores': wechat_user.addscore_set.all(), 'url': url, 'max_value': max_value}
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
        if created:
            user.score += score
            user.save()
        if user.score >= 3000:
            prize, created = Prize.objects.get_or_create(user=user, prize=u'1')
            if created:
                wechat = WechatMPAuth()
                data = {
                    "first": {
                        "value": u'恭喜您，您的小伙伴已帮您集满3000ml洗衣液，您已获得奖品。',
                        "color": "#173177"  # 标准蓝色
                    },
                    "keyword1": {
                        "value": u'顶奇夏日狂欢节',
                    },
                    "keyword2": {
                        "value": u'顶奇焕彩柔顺洗衣液3kg装一瓶',
                    },
                    "remark": {
                        "value": u"请点击公众号底栏中的兑换奖品查看兑换方式。邀请更多好友赢取更多大奖!",
                    }
                }
                res = wechat.send_template_message(settings.MESSAGE_TEMPLATE['prize'], None, data,
                                           user.openid)
    context = {'score': score, 'created': created, 'error': error, 'name': name, 'avatar': avatar}
    return JsonResponse(context)


@wechat_only
def join(request, openid):
    wechat = WechatMPAuth()
    info = wechat.get_mp_user_info(openid)
    map(lambda x: info.pop(x), ['subscribe_time', 'remark', 'groupid', 'subscribe', 'language', 'tagid_list', 'openid'])
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
    ranked_users = WechatUser.objects.filter(score__gt=0).order_by('-score')[:50]
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


def error404(request):
    return HttpResponse('你访问了不存在的页面。')


def error500(request):
    return HttpResponse('出错了,请重试。')
