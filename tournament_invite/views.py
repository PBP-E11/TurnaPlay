from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import TournamentInvite
from tournament_registration.models import TournamentRegistration, TeamMember
from game_account.models import GameAccount

# ========= Helpers =========

def _is_user_team_leader(user, team: TournamentRegistration) -> bool:
    """
    Cek apakah 'user' adalah leader dari 'team' tersebut.
    Berdasar model TeamMember: is_leader=True dan GameAccount.user == user
    """
    return TeamMember.objects.filter(
        team=team,
        is_leader=True,
        game_account__user=user,
    ).exists()

def _team_game(team: TournamentRegistration):
    return team.tournament.tournament_format.game

# ========= Pages =========

@login_required
def invite_list(request):
    # Incoming = undangan yang ditujukan ke user ini
    incoming = TournamentInvite.objects.filter(
        user_account=request.user
    ).select_related('tournament_registration__tournament__tournament_format__game').order_by('-created_at')

    # Outgoing = undangan yang dikirim dari tim yang dipimpin user ini
    outgoing = TournamentInvite.objects.filter(
        tournament_registration__members__is_leader=True,
        tournament_registration__members__game_account__user=request.user
    ).select_related('tournament_registration__tournament__tournament_format__game', 'user_account').order_by('-created_at').distinct()

    # Kumpulan team yang user ini pimpin -> untuk form create invite
    my_leading_teams = TournamentRegistration.objects.filter(
        members__is_leader=True,
        members__game_account__user=request.user
    ).select_related('tournament__tournament_format__game').distinct()

    context = {
        'incoming': incoming,
        'outgoing': outgoing,
        'my_leading_teams': my_leading_teams,
    }
    return render(request, 'tournament_invite/invite_list.html', context)

# ========= AJAX / Utilities =========

@login_required
def check_new_invite(request):
    # Hitung pending incoming invites
    pending = TournamentInvite.objects.filter(
        user_account=request.user, status=TournamentInvite.Status.PENDING
    ).count()
    return JsonResponse({'pending': pending})

# ========= Actions =========

@login_required
@transaction.atomic
def create_invite(request):
    """
    Leader mengundang user lain ke tim (TournamentRegistration).
    Input minimal (POST):
      - team_id (UUID TournamentRegistration)
      - user_id (UUID UserAccount) atau username
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    team_id = request.POST.get('team_id')
    user_id = request.POST.get('user_id')
    username = request.POST.get('username')

    if not team_id or not (user_id or username):
        return HttpResponseBadRequest('team_id and user_id/username are required')

    team = get_object_or_404(TournamentRegistration, pk=team_id)

    # hanya leader tim yang boleh undang
    if not _is_user_team_leader(request.user, team):
        return HttpResponseForbidden('Only team leader can invite')

    # resolve invited user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if user_id:
        invited_user = get_object_or_404(User, pk=user_id)
    else:
        invited_user = get_object_or_404(User, username=username)

    # larangan mengundang diri sendiri
    if invited_user == request.user:
        return HttpResponseBadRequest("You cannot invite yourself.")

    # Cek sudah jadi member tim lain di turnamen yang sama?
    tournament = team.tournament
    already_joined = TeamMember.objects.filter(
        game_account__user=invited_user,
        team__tournament=tournament,
    ).exists()
    if already_joined:
        return HttpResponseBadRequest("User already joined a team for this tournament.")

    # Buat/temukan invite pending
    inv, created = TournamentInvite.objects.get_or_create(
        user_account=invited_user,
        tournament_registration=team,
        status=TournamentInvite.Status.PENDING,
    )

    return redirect('tournament_invite:invite_list')

@login_required
@transaction.atomic
def accept_invite(request, invite_id):
    """
    Penerima menerima undangan.
    Wajib memilih GameAccount milik dirinya yang sesuai dengan game turnamen.
    - GET: render mini-modal (fragment) untuk pilih game account (jika tidak kirim id)
    - POST: butuh 'game_account_id'
    """
    inv = get_object_or_404(
        TournamentInvite,
        pk=invite_id,
        user_account=request.user,
        status=TournamentInvite.Status.PENDING
    )

    team = inv.tournament_registration
    game = _team_game(team)

    if request.method == 'GET' and not request.GET.get('game_account_id'):
        # Kirim fragment modal
        my_accounts = GameAccount.objects.filter(user=request.user, game=game, active=True)
        return render(request, 'tournament_invite/_choose_game_account.html', {
            'invite': inv,
            'game': game,
            'accounts': my_accounts,
        })

    # Ambil game_account_id dari POST/GET (modal submit)
    game_account_id = request.POST.get('game_account_id') or request.GET.get('game_account_id')
    if not game_account_id:
        return HttpResponseBadRequest('game_account_id is required')

    ga = get_object_or_404(GameAccount, pk=game_account_id, user=request.user, game=game, active=True)

    # Tambah ke anggota tim (is_leader=False)
    TeamMember.objects.create(
        game_account=ga,
        team=team,
        is_leader=False,
    )

    inv.status = TournamentInvite.Status.ACCEPTED
    inv.save()

    return HttpResponseRedirect(reverse('tournament_invite:invite_list'))

@login_required
@transaction.atomic
def reject_invite(request, invite_id):
    inv = get_object_or_404(
        TournamentInvite,
        pk=invite_id,
        user_account=request.user,
        status=TournamentInvite.Status.PENDING
    )
    inv.status = TournamentInvite.Status.REJECTED
    inv.save()
    return HttpResponseRedirect(reverse('tournament_invite:invite_list'))

@login_required
@transaction.atomic
def cancel_invite(request, invite_id):
    # Leader membatalkan undangan dari timnya.
    inv = get_object_or_404(TournamentInvite, pk=invite_id)

    team = inv.tournament_registration
    if not _is_user_team_leader(request.user, team):
        return HttpResponseForbidden('Only team leader can cancel')

    # Boleh batalkan apapun yang masih pending
    if inv.status != TournamentInvite.Status.PENDING:
        return HttpResponseBadRequest('Only pending invites can be canceled')

    inv.delete()
    return HttpResponseRedirect(reverse('tournament_invite:invite_list'))