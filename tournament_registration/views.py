import uuid
from django.http import HttpRequest, Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import TournamentRegistration, TeamMember
from user_account.models import UserAccount
from tournaments.models import Tournament
from .forms import TeamNameForm, LeaderForm, MemberForm

@require_http_methods(['GET', 'POST'])
@login_required
def new_team_form(request: HttpRequest, tournament_id: uuid.UUID) -> HttpResponse:
    team_form = TeamNameForm(request.POST or None)
    leader_form = LeaderForm(
        request.POST or {'username': request.user.username},
        readonly=False,
        user=request.user,
    )
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    membership = TeamMember.objects.filter(
        game_account__user=request.user,
    ).select_related('team').first()
    if membership is not None:
        return redirect('team:edit_team_form', team_id=membership.team.id)

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
    # fetch the team
    team = get_object_or_404(TournamentRegistration, pk=team_id)

    members_qs = team.members.select_related("game_account__user")

    # find leader TeamMember (if any)
    leader_member = members_qs.filter(is_leader=True).first()

    # Team name form (this is the one we accept POSTs for)
    team_form = TeamNameForm(request.POST or None, instance=team)

    if request.method == "POST" and team_form.is_valid():
        # (optional) permission check: only allow team leader to rename
        if leader_member and getattr(leader_member.game_account, "user", None) != request.user:
            return HttpResponseForbidden("Only the team leader can edit the team.")

        # save name change
        team_form.save()
        # redirect to the same page to avoid double submit
        return redirect("team:edit_team_form", team_id=team.id)

    # Build a display-only leader form (not used for POST processing here).
    # We use initial so the form renders current values; LeaderForm disables username
    # so it acts as a read-only display.
    leader_initial = {}
    if leader_member:
        leader_initial = {
            "username": getattr(leader_member.game_account.user, "username", ""),
            "game_account": leader_member.game_account_id,
        }

    # Pass user param so the form's queryset for game_account is restricted (if you've implemented that)
    leader_form = LeaderForm(initial=leader_initial, user=leader_member.game_account.user if leader_member else request.user)

    context = {
        "team": team,
        "team_form": team_form,
        "leader_form": leader_form,   # display only — not processed on POST here
        "members": members_qs,        # ordered members to render in template
    }
    return render(request, "team/edit_form.html", context)
