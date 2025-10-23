import json
from .models import GameAccount
from .forms import GameAccountForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from django.views import View
from django.db import transaction, IntegrityError
from django.shortcuts import render
from tournaments.models import Game

@require_http_methods(["GET", "POST"])
def game_accounts_list_create(request):
    # GET -> list (supports ?game=<id>)
    if request.method == 'GET':
        game_id = request.GET.get('game')
        if game_id:
            qs = GameAccount.objects.filter(game__id=game_id, active=True)
        elif request.user.is_authenticated:
            qs = GameAccount.objects.filter(user=request.user)
        else:
            qs = GameAccount.objects.none()
        data = list(qs.values('id', 'user_id', 'game_id', 'ingame_name', 'active'))
        return JsonResponse(data, safe=False, status=200)

    # POST -> create
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        form = GameAccountForm(data=payload)
        if form.is_valid():
            ga = form.save(commit=False)
            ga.user = request.user
            try:
                with transaction.atomic():
                    ga.save()
            except IntegrityError:
                return JsonResponse({'detail': 'Account with that in-game name already exists for this game.'}, status=400)
            return JsonResponse({'id': str(ga.id), 'user': ga.user_id, 'game': str(ga.game_id), 'ingame_name': ga.ingame_name, 'active': ga.active}, status=201)
        return JsonResponse({'errors': form.errors}, status=400)

class GameAccountDetail(View):
    def get(self, request, pk):
        ga = get_object_or_404(GameAccount, pk=pk)
        return JsonResponse(model_to_dict(ga, fields=['id','user','game','ingame_name','active']))

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        ga = get_object_or_404(GameAccount, pk=pk)
        if ga.user != request.user and not request.user.is_staff:
            return HttpResponseForbidden()
        ga.active = False
        ga.save()   
        return JsonResponse({}, status=204)
    
@login_required
def select_widget(request):
    game_id = request.GET.get('game')
    qs = GameAccount.objects.filter(user=request.user, active=True)
    if game_id:
        qs = qs.filter(game__id=game_id, active=True)
    data = list(qs.values('id', 'game_id', 'ingame_name'))
    return JsonResponse(data, safe=False)


@login_required
def list_page(request):
    games = Game.objects.all()
    return render(request, 'game_account/list.html', {'games': games})


@login_required
def form_partial(request):
    # return the form fragment used by the modal (games list required)
    games = Game.objects.all()
    return render(request, 'game_account/_form.html', {'games': games})


@login_required
def detail_page(request, pk):
    ga = get_object_or_404(GameAccount, pk=pk)
    return render(request, 'game_account/detail.html', {'ga': ga})