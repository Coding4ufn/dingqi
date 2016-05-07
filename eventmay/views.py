# coding: utf-8
from django.shortcuts import render


def user_page(request, fakeid):
    """个人页面"""
    context = {}
    return render(request, '', context)


def rank(request):
    """排名页面"""
    context = {}
    return render(request, '', context)