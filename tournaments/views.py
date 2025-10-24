from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from .models import Tournament
from .forms import TournamentCreationForm
from django.http import JsonResponse
from .models import TournamentFormat
from django.shortcuts import get_object_or_404


def show_main(request):
    # Query tournaments ordered by date (newest first) and paginate
    tournaments_qs = Tournament.objects.order_by('-tournament_date', 'tournament_name')
    paginator = Paginator(tournaments_qs, 9)  #9 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'tournaments': page_obj.object_list,
        'page_obj': page_obj,
    }

    # Compute a safe permission flag for showing the Create button in templates
    user = request.user
    can_create = False
    if user.is_authenticated:
        if getattr(user, 'is_staff', False):
            can_create = True
        else:
            ua = getattr(user, 'useraccount', None)
            if ua and getattr(ua, 'role', None) == 'organizer':
                can_create = True
            elif getattr(user, 'role', None) == 'organizer':
                can_create = True

    context['can_create'] = can_create

    return render(request, "main.html", context)


def tournament_create(request):
    """Function-based view to display and process the tournament creation form."""
    if request.method == 'POST':
        form = TournamentCreationForm(request.POST)
        if form.is_valid():
            # Set the organizer to the current user (assuming the organizer is a User model)
            tournament = form.save(commit=False)
            tournament.organizer = request.user  # Assuming 'organizer' is a ForeignKey to the User model
            tournament.save()
            # Redirect to main tournament list so the newly created tournament appears
            return redirect(reverse('tournaments:show_main'))
    else:
        form = TournamentCreationForm()

    return render(request, 'tournament_form.html', {'form': form, 'title': 'Create New Tournament'})


def tournament_list_json(request):
    """Paginated JSON endpoint for client-side "Next" loading.

    Returns a JSON object with keys:
      - tournaments: list of objects with id, detail_url, tournament_name, tournament_date, banner_url (when available)
      - has_next: boolean
      - next_page: optional int (next page number) — client will prefer this when present
    """
    page_number = request.GET.get('page', 1)
    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    tournaments_qs = Tournament.objects.order_by('-tournament_date', 'tournament_name')
    paginator = Paginator(tournaments_qs, 9)
    page = paginator.get_page(page_number)

    # Build a serializable list of lightweight tournament dicts the client expects
    tournaments_list = []
    for t in page.object_list:
        tournaments_list.append({
            'id': str(t.pk),
            'detail_url': request.build_absolute_uri(reverse('tournaments:tournament-detail', args=[t.pk])),
            'tournament_name': t.tournament_name,
            'tournament_date': t.tournament_date.isoformat() if t.tournament_date else None,
            # banner may be an ImageField — prefer URL if available
            'banner_url': (t.banner.url if getattr(t, 'banner', None) and hasattr(t.banner, 'url') else None),
        })

    response_data = {
        'tournaments': tournaments_list,
        'has_next': page.has_next(),
        'page': page.number,
        'page_size': paginator.per_page,
        'total_pages': paginator.num_pages,
    }
    if page.has_next():
        response_data['next_page'] = page.next_page_number()
    if page.has_previous():
        response_data['previous_page'] = page.previous_page_number()

    return JsonResponse(response_data)


def formats_for_game(request, game_id):
    """Return a small JSON list of formats for the given game (used by the create form JS).

    Only GET is supported. If other methods are used, return 405.
    """
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)

    formats = TournamentFormat.objects.filter(game_id=game_id).values('id', 'name', 'team_size')
    # Convert QuerySet values() into a list so JsonResponse can serialize it
    return JsonResponse({'formats': list(formats)})


def tournament_detail(request, pk):
    """Simple detail view for a single tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    return render(request, 'tournament_detail.html', {'tournament': tournament})

