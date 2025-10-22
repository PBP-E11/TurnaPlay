from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import TournamentInvite

@login_required
def invite_list(request):
    # Undangan yang DITERIMA user ini
    incoming = TournamentInvite.objects.filter(
        user_account__user=request.user
    ).order_by('-created_at')

    # Undangan yang DIKIRIM tim milik user ini
    # NOTE: sesuaikan field "leader" sesuai schema modul tournament regist
    try:
        outgoing = TournamentInvite.objects.filter(
            tournament_registration__leader__user=request.user
        ).order_by('-created_at')
    except Exception:
        outgoing = []

    return render(request, 'tournament_invite/invite_list.html', {
        'incoming': incoming,
        'outgoing': outgoing,
    })

@login_required
def check_new_invite(request):
    pending = TournamentInvite.objects.filter(
        user_account__user=request.user, status='pending'
    ).count()
    return JsonResponse({'pending': pending})

@login_required
def accept_invite(request, invite_id):
    inv = get_object_or_404(
        TournamentInvite,
        pk=invite_id,
        user_account__user=request.user,
        status='pending'
    )
    # TODO (nanti): minta pilih GameAccount lalu simpan
    inv.status = 'accepted'
    inv.save()
    return HttpResponseRedirect(reverse('tournament_invite:invite_list'))

@login_required
def reject_invite(request, invite_id):
    inv = get_object_or_404(
        TournamentInvite,
        pk=invite_id,
        user_account__user=request.user,
        status='pending'
    )
    inv.status = 'rejected'
    inv.save()
    return HttpResponseRedirect(reverse('tournament_invite:invite_list'))