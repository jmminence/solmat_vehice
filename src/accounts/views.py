# -*- coding: utf-8 -*-
from django.shortcuts import render
from utils.functions import renderjson
from .forms import UserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import View
from django.contrib.auth.models import User, Permission
from accounts.models import UserProfile
from utils.functions import renderjson as render2
from django.contrib import messages

import json
import random
import string


class PERMISOS(View):
    http_method_names = ['post']

    def post(self, request):
        var_post = request.POST.copy()
        permisos = json.loads(var_post['permisos'])
        user_id = var_post['user_id']

        if not user_id:
            return renderjson({
                'error': 1,
                'message': 'El id de usuario es requerido.'
            })

        user = User.objects.get(pk=user_id)
        user.user_permissions.clear()

        if permisos:
            for perm in permisos:
                user.user_permissions.add(perm)

        users = User.objects.all().exclude(pk=request.user.pk).exclude(
            is_superuser=1).exclude(is_active=0)
        response = []
        for user in users:
            perms = []
            his_perms = Permission.objects.filter(user=user.pk)
            for perm in his_perms:
                perms.append({'id': perm.id, 'name': perm.name})

            response.append({
                'first_name': user.first_name.capitalize(),
                'last_name': user.last_name.capitalize(),
                'email': user.email,
                'is_active': user.is_active,
                'id': user.pk,
                'perms': perms,
            })

        return render2({
            'error': 0,
            'message': 'Permisos actualizados.',
            'response': json.dumps(response)
        })


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                try:
                    login(request, user)
                    return HttpResponseRedirect('/')
                except Exception as e:
                    print("Error: ", e)
            else:
                return render(
                    request, 'accounts/login.html', {
                        'login_message':
                        'Estimado usuario, tu cuenta se encuentra desactivada.'
                    })
        else:
            return render(
                request, 'accounts/login.html', {
                    'login_message':
                    'Es posible que tu usuario o contraseña sean incorrectas, intenta nuevamente.'
                })
    else:
        return render(request, 'accounts/login.html', {})


# @login_required
def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render(
        request, 'accounts/register.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'registered': registered
        })


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


class USER(View):
    http_method_names = ['get', 'post', 'put', 'delete']

    def get(self, request, id=None):
        usuario = User.objects.get(pk=id)
        user_profile = UserProfile.objects.filter(user_id=id).first()
        return renderjson({
            'error': 0,
            'first_name': usuario.first_name.capitalize(),
            'last_name': usuario.last_name.capitalize(),
            'email': usuario.email,
            'is_active': usuario.is_active,
            'is_superuser': usuario.is_superuser,
            'account_type': user_profile.account_type
        })

    def post(self, request):
        var_post = request.POST.copy()
        first_name = var_post['first_name']
        last_name = var_post['last_name']
        email = var_post['email']
        profile = var_post['profile']
        is_admin = True
        is_active = True
        auxUsername = True
        checkMail = User.objects.filter(email=email).count()
        if checkMail > 0:
            return renderjson({
                'error':
                1,
                'message':
                'El correo electrónico ya ha sido utilizado para crear otra cuenta.'
            })
        username = ''.join(
            random.choice(string.ascii_uppercase + string.digits +
                          string.ascii_lowercase) for x in range(20))
        while auxUsername:
            aux_user = User.objects.filter(username=username).count()
            if aux_user == 0:
                auxUsername = False
            else:
                username = ''.join(
                    random.choice(string.ascii_uppercase + string.digits +
                                  string.ascii_lowercase) for x in range(20))
        contrasena = '123456'

        try:
            if is_admin:
                newUser = User.objects.create_superuser(
                    username, email, contrasena)
                newUser.is_active = is_active
                newUser.save()
            else:
                newUser = User.objects.create_user(username, email, contrasena)
                newUser.is_active = is_active
                newUser.save()
        except Exception as e:
            return renderjson({'error': 1, 'message': str(e)})

        # newUser.is_active = False
        confirmation_code = ''.join(
            random.choice(string.ascii_uppercase + string.digits +
                          string.ascii_lowercase) for x in range(60))
        aux = True
        while aux:
            aux_user = UserProfile.objects.filter(
                confirmation_code=confirmation_code).count()
            if aux_user == 0:
                aux = False
            else:
                confirmation_code = ''.join(
                    random.choice(string.ascii_uppercase + string.digits +
                                  string.ascii_lowercase) for x in range(60))
        # subject = "Account confirmation"
        # to = [email]
        # from_email = 'no-reply@dataqu.cl'

        # ctx = {
        #     'code': confirmation_code,
        #     'email': email,
        #     'username': username,
        #     'url':settings.SITE_URL
        # }

        # message = get_template('accounts/email_confirmation.html').render(Context(ctx))
        # msg = EmailMultiAlternatives(subject,message,from_email,to)
        # msg.content_subtype="html"
        # msg.send()
        grupo = request.user.groups.first()

        newUser.first_name = first_name
        newUser.last_name = last_name
        newUser.save()
        userProfile = UserProfile(
            user=newUser,
            state=1,
            account_type=profile,
            confirmation_code=confirmation_code)
        userProfile.save()
        # newUser.groups.add(grupo) # esta linea esta dando error por que no existen grupos
        # userRoles = UserRoles.objects.get(role=userProfile.role)
        return render2({
            'error':
            0,
            'message':
            'Usuario añadido con éxito.',
            'nombre':
            newUser.first_name.capitalize() + ' ' +
            newUser.last_name.capitalize(),
            'email':
            newUser.email,
            'id':
            newUser.id,
            'is_superuser':
            newUser.is_superuser,
            'is_active':
            newUser.is_active
        })

    def put(self, request, id=None):
        var_put = request.PUT.copy()
        first_name = var_put['first_name']
        last_name = var_put['last_name']
        email = var_put['email']
        profile = var_put['profile']
        # is_admin = var_put.get('admin', False)
        # is_active = var_put.get('active', False)
        user = User.objects.get(pk=id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_superuser = True
        user.is_active = True
        user.save()
        user_profile = UserProfile.objects.filter(user_id=id).first()
        user_profile.account_type = profile
        user_profile.save()

        return renderjson({
            'error':
            0,
            'message':
            'Usuario actualizado con éxito.',
            'nombre':
            user.first_name.capitalize() + ' ' + user.last_name.capitalize(),
            'email':
            user.email,
            'is_superuser':
            user.is_superuser,
            'is_active':
            user.is_active,
            'id':
            user.id
        })

    def delete(self, request, id=None):
        try:
            user = User.objects.get(pk=id).delete()
            return renderjson({
                'error': 0,
                'message': 'Usuario eliminado exitosamente.'
            })
        except Exception as e:
            return renderjson({
                'error': 1,
                'message': 'Error al eliminar el usuario.'
            })


def userVerification(request, confirmation_code=None):
    dataqu_user = dataquUser.objects.get(confirmation_code=confirmation_code)
    user = dataqu_user.user
    user.is_active = True
    user.save()
    dataqu_user.user = user
    dataqu_user.save

    return render2(request, "confirmacion.html")


@login_required
def user_profile(request):
    user = request.user
    userProfile = UserProfile.objects.get(user=user)
    grupo = user.groups.first()
    nombre = user.first_name.capitalize() + " " + user.last_name.capitalize()
    hayFoto = 0
    signature = ""
    if userProfile.signature == None:
        hayFoto = 0
    elif userProfile.signature == '':
        hayFoto = 0
    else:
        hayFoto = 1
        signature = userProfile.signature.url
    return render(
        request, 'accounts/profile.html', {
            'group': grupo.name if grupo else None,
            'name': nombre,
            'first_name': user.first_name.capitalize(),
            'last_name': user.last_name.capitalize(),
            'email': user.email,
            'rut': userProfile.rut,
            'phone': userProfile.phone,
            'hayFoto': hayFoto,
            'signature': signature
        })


@login_required
def change_password(request):
    var_post = request.POST.copy()
    user = authenticate(
        username=request.user.username, password=request.POST['old_password'])
    pass1 = var_post['new_password1']
    pass2 = var_post['new_password2']
    if user:
        if pass1 == pass2:
            user.set_password(pass1)
            user.save()
            user = authenticate(username=request.user.username, password=pass1)
            login(request, user)
            return render2({
                'error': 0,
                'message': "Contraseña cambiada con éxito."
            })
        else:
            return render2({
                'error': 1,
                'message': "Las nuevas contraseñas no coinciden."
            })
    else:
        return render2({
            'error': 1,
            'message': "La contraseña antigua no coincide."
        })


@login_required
def change_info(request):
    var_post = request.POST.copy()
    first_name = var_post['first_name']
    last_name = var_post['last_name']
    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    rut = var_post['rut']
    phone = var_post['phone']
    firma = request.FILES.get('firma', None)
    userProfile = UserProfile.objects.get(user=user)
    userProfile.rut = rut
    userProfile.phone = phone
    if firma:
        userProfile.signature = firma
    user.save()
    userProfile.save()
    nombre = user.first_name.capitalize() + " " + user.last_name.capitalize()
    messages.success(request, 'Datos personales cambiados correctamente')
    return render2({'error': 0})
