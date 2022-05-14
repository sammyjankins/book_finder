from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from users.services import register_user, update_profile, bind_tele_id


def register_view(request):
    if request.method == "POST":
        form = register_user(request)
        if form.is_valid():
            return redirect('login')
        else:
            form = UserRegisterForm(request.POST)
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == "POST":
        u_form, p_form = update_profile(request)
        if u_form.is_valid() and p_form.is_valid():
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'u_form': u_form, 'p_form': p_form, })


@login_required
def bind_tele_id_view(request, **kwargs):
    bind_tele_id(request, **kwargs)
    return render(request, 'users/profile.html', )
