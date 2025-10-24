import uuid
from django.http import HttpRequest, Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import TournamentRegistration, TeamMember
from user_account.models import UserAccount
from tournaments.models import Tournament
from .forms import TeamNameForm, MemberForm, MemberForm

@require_http_methods(['GET', 'POST'])
@login_required
def new_team_form(request: HttpRequest, tournament_id: uuid.UUID) -> HttpResponse:
    # Make sure tournament actually exist
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    # Initialize forms
    team_form = TeamNameForm(initial=request.POST or None)
    leader_form = MemberForm(
        request.POST or None,
        user=request.user,
        tournament=tournament,
    )

    # Check if user is already in a team, if so don't allow creating new team
    membership = TeamMember.objects.filter(
        game_account__user=request.user,
        team__tournament=tournament,
    ).select_related('team').first()
    if membership is not None:
        return redirect('team:edit_team_form', team_id=membership.team.id)

    # If tournament form is complete
    if team_form.is_valid() and leader_form.is_valid() and request.method == 'POST':
        if leader_form.cleaned_data['username'] != request.user.username:
            return HttpResponseForbidden('Cannot create team as another user')
        if leader_form.cleaned_data['game_account'].user != request.user:
            return HttpResponseForbidden('This game account does not belong to the user logged in')

        team_entry = team_form.save(commit=False)
        team_entry.tournament = tournament
        team_entry.save()

        TeamMember.objects.create(
            is_leader=True,
            game_account=leader_form.cleaned_data['game_account'],
            team=team_entry,
        )
        return edit_team_form(request, team_entry.id)

    context = {
        'tournament': tournament,
        'team_form': team_form,
        'leader_form': leader_form,
    }
    return render(request, 'team/new_form.html', context)


@require_http_methods(["GET", "POST"])
@login_required
def edit_team_form(request: HttpRequest, team_id: uuid.UUID) -> HttpResponse:
    # Fetch the team
    team = get_object_or_404(TournamentRegistration, pk=team_id)
    members_qs = team.members.select_related("game_account__user")
    # Find leader TeamMember (if any)
    leader = members_qs.filter(is_leader=True).first()

    # Before continuing, check if user is actually allowed to do anything
    if not _is_user_in_team(request.user, team):
        return HttpResponseForbidden('You are not part of this team')

    # Forms
    team_form = TeamNameForm(request.POST or None, instance=team)
    leader_form = MemberForm(
        request.POST or None,
        user=leader.game_account.user,
        team=team,
        instance=leader,
    )

    if request.method == "POST" and team_form.is_valid():
        # (optional) permission check: only allow team leader to rename
        if leader and getattr(leader.game_account, "user", None) != request.user:
            return HttpResponseForbidden("Only the team leader can edit the team.")

        # save name change
        team_form.save()
        # redirect to the same page to avoid double submit
        return redirect("team:edit_team_form", team_id=team.id)

    context = {
        "team": team,
        "team_form": team_form,
        "leader_form": leader_form,
        "members": members_qs,
        "tournament": team.tournament,
        "is_leader": _is_user_team_leader(request.user, team),
    }
    return render(request, "team/edit_form.html", context)

@require_http_methods(["GET"])
def list_members(request: HttpRequest, team_id: uuid.UUID) -> JsonResponse:
    try:
        team = TournamentRegistration.objects.get(pk=team_id)
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Not logged in'}, status=403)
        if not _is_user_in_team(request.user, team):
            return JsonResponse({'detail': 'Not part of team'}, status=403)
        data = [{
            'game_account_id': member.game_account.id,
            'username': member.game_account.user.username,
            'ingame_name': member.game_account.ingame_name,
        } for member in team.members.all()]
        return JsonResponse(data, safe=False)
    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

@require_http_methods(["POST"])
def leave_team(request: HttpRequest, team_id: uuid.UUID) -> JsonResponse:
    try:
        team = TournamentRegistration.objects.get(pk=team_id)
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Not logged in'}, status=403)
        if not _is_user_in_team(request.user, team):
            return JsonResponse({'detail': 'Not part of team'}, status=403)

        if _is_user_team_leader(request.user, team):
            team.delete()
        else:
            team.members.filter(game_account__user=request.user).delete()

        return JsonResponse({'detail': 'Ok'}, status=200)
    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

@require_http_methods(["POST"])
def kick_member(request: HttpRequest, team_id: uuid.UUID):
    try:
        team = TournamentRegistration.objects.get(pk=team_id)
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Not logged in'}, status=403)
        if not _is_user_in_team(request.user, team):
            return JsonResponse({'detail': 'Not part of team'}, status=403)

        if not _is_user_team_leader(request.user, team):
            return JsonResponse({'detail': 'Only leader can kick members'}, status=403)

        member_id = request.POST.get("member_id")
        if not member_id:
            return JsonResponse({'detail': 'Missing member_id'}, status=400)

        deleted, _ = team.members.filter(game_account__id=member_id).delete()
        if not deleted:
            return JsonResponse({'detail': 'Member not found'}, status=404)

        return JsonResponse({'detail': 'Ok'}, status=200)

    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

# Mksh karla :>
def _is_user_team_leader(user: UserAccount, team: TournamentRegistration) -> bool:
    """
    Cek apakah 'user' adalah leader dari 'team' tersebut.
    Berdasar model TeamMember: is_leader=True dan GameAccount.user == user
    """
    return TeamMember.objects.filter(
        team=team,
        is_leader=True,
        game_account__user=user,
    ).exists()

def _is_user_in_team(user: UserAccount, team: TournamentRegistration) -> bool:
    return TeamMember.objects.filter(
        team=team,
        game_account__user=user,
    ).exists()

@require_http_methods(["GET"])
def tournament_details(request: HttpRequest, tournament_id: uuid.UUID) -> HttpResponse:
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    context = {
        'tournament': tournament
    }
    return render(request, 'team/tournament_details.html', context)
