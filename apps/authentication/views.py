from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages


class LoginView(View):
    template_name = 'authentication/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.est_actif_cie:
                messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                return render(request, self.template_name)
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        messages.error(request, "Identifiant ou mot de passe incorrect.")
        return render(request, self.template_name, {'username': username})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('authentication:login')


class ProfilView(LoginRequiredMixin, View):
    template_name = 'authentication/profil.html'

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})


class MarquerAnnonceVueView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vues = request.session.get('annonces_vues', [])
        if pk not in vues:
            vues.append(pk)
            request.session['annonces_vues'] = vues
        from django.http import JsonResponse
        return JsonResponse({'ok': True})
