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
            order=0
        )
        return edit_team_form(request, team_entry.id)

    context = {
        'tournament': tournament,
        'team_form': team_form,
        'leader_form': leader_form,
    }
    return render(request, 'team/new_form.html', context)


@require_http_methods(['GET', 'POST'])
@login_required
def edit_team_form(request: HttpRequest, team_id: uuid.UUID) -> HttpResponse:
    team = get_object_or_404(TournamentRegistration, pk=team_id)
    members = TournamentRegistration.members

    tournament = team.tournament
    team_form = TeamNameForm(request.POST or None, instance=team)
    leader_form = LeaderForm(request.POST or None, instance=members.first(order=0))
