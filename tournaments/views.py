from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from .models import Tournament
from .forms import TournamentCreationForm
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
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
    user_is_admin = False
    user_is_organizer = False

    if user.is_authenticated:
        # Check for admin first (is_staff is from your UserAccount model)
        if getattr(user, 'is_staff', False):
            can_create = True
            user_is_admin = True
        # Check for organizer (is_organizer() is from your UserAccount model)
        elif hasattr(user, 'is_organizer') and user.is_organizer():
            can_create = True
            user_is_organizer = True
            
    context['can_create'] = can_create
    
    context['user_is_admin'] = user_is_admin
    context['user_is_organizer'] = user_is_organizer
    context['current_user_id'] = str(user.id) if user.is_authenticated else 'None'

    return render(request, "main.html", context)

@login_required(login_url='/accounts/login')
def tournament_create(request):
    """Function-based view to display and process the tournament creation form."""

    # User must be an Admin (is_staff) or an Organizer
    if not (request.user.is_staff or (hasattr(request.user, 'is_organizer') and request.user.is_organizer())):
        return HttpResponseForbidden("You do not have permission to create a tournament.")
  
    if request.method == 'POST':
        # Accept file uploads (banner) via request.FILES
        form = TournamentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Don't save to DB yet
            tournament = form.save(commit=False)

            tournament.organizer = request.user
            # If a banner file was uploaded, store it using default storage and
            # write its public URL into the model's banner (a URLField).
            banner_file = request.FILES.get('banner')
            if banner_file:
                from django.core.files.storage import default_storage
                # build a safe path within MEDIA (e.g. 'banners/<filename>')
                save_path = f"banners/{banner_file.name}"
                name = default_storage.save(save_path, banner_file)
                # default_storage.url() returns a URL that can be used in templates
                tournament.banner = default_storage.url(name)

            tournament.save()
            return redirect(reverse('tournaments:show_main'))
    else:
        form = TournamentCreationForm()

    return render(request, 'tournament_form.html', {'form': form, 'title': 'Create New Tournament'})

@login_required
def tournament_update(request, pk):
    """View to update an existing tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)

    # --- PERMISSION CHECK ---
    is_admin = request.user.is_staff
    is_organizer = hasattr(request.user, 'is_organizer') and request.user.is_organizer()
    is_owner = (tournament.organizer == request.user)

    # Allow if user is an Admin OR (is an Organizer AND is the owner)
    if not (is_admin or (is_organizer and is_owner)):
        return HttpResponseForbidden("You do not have permission to edit this tournament.")
    # --- END CHECK ---
        
    if request.method == 'POST':
        # Pass instance=tournament to update the existing object
        form = TournamentCreationForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            t = form.save(commit=False)
            banner_file = request.FILES.get('banner')
            if banner_file:
                from django.core.files.storage import default_storage
                save_path = f"banners/{banner_file.name}"
                name = default_storage.save(save_path, banner_file)
                t.banner = default_storage.url(name)
            t.save()
            return redirect(reverse('tournaments:tournament-detail', args=[tournament.pk]))
    else:
        # Pre-populate the form with the tournament's existing data
        form = TournamentCreationForm(instance=tournament)

    # Reuse the same form template
    return render(request, 'tournament_form.html', {'form': form, 'title': f'Edit {tournament.tournament_name}'})

# --- NEW VIEW ---
@login_required
def tournament_delete(request, pk):
    """View to delete an existing tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)

    # --- PERMISSION CHECK (Same as update) ---
    is_admin = request.user.is_staff
    is_organizer = hasattr(request.user, 'is_organizer') and request.user.is_organizer()
    is_owner = (tournament.organizer == request.user)

    # Allow if user is an Admin OR (is an Organizer AND is the owner)
    if not (is_admin or (is_organizer and is_owner)):
        return HttpResponseForbidden("You do not have permission to delete this tournament.")
    # --- END CHECK ---

    if request.method == 'POST':
        # This is the confirmation step
        tournament.delete()
        return redirect(reverse('tournaments:show_main'))

    # GET request: show the confirmation page
    # We need a new template for this: 'tournament_confirm_delete.html'
    return render(request, 'tournament_confirm_delete.html', {'tournament': tournament})

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

    game_name = request.GET.get('game_name', None)
    if game_name:
        tournaments_qs = tournaments_qs.filter(tournament_format__game__name__icontains=game_name)
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
            # banner stored as a URL string in the model (or empty). Use it if present.
            'banner_url': (t.banner if getattr(t, 'banner', None) else None),
            'is_active': t.is_active,
            'organizer_id': str(t.organizer_id) if t.organizer_id else None,
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

