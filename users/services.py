from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from users.models import Profile


def register_user(request):
    form = UserRegisterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Аккаунт успешно зарегистрирован! Войдите чтобы продолжить работу.')
    return form


def update_profile(request):
    u_form = UserUpdateForm(request.POST, instance=request.user)
    p_form = ProfileUpdateForm(request.POST,
                               request.FILES,
                               instance=request.user.profile)
    if u_form.is_valid() and p_form.is_valid():
        u_form.save()
        p_form.save()
        messages.success(request, f'Данные обновлены!')
    return u_form, p_form


def bind_tele_id(request, **kwargs):
    if request.method == "GET":
        profile = Profile.objects.filter(user=request.user).first()
        for binded in Profile.objects.filter(tele_id=kwargs['tele_id']):
            binded.tele_id = None
        profile.tele_id = kwargs['tele_id']
        profile.save()
        print(profile)
    u_form = UserUpdateForm(request.POST, instance=request.user)
    p_form = ProfileUpdateForm(request.POST,
                               request.FILES,
                               instance=request.user.profile)
    return u_form, p_form
