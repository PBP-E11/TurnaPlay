# In your_app/forms.py
from django import forms
from .models import Tournament, Game, TournamentFormat
from django.utils import timezone

TAILWIND_INPUT = "block w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-slate-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
TAILWIND_TEXTAREA = "block w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-slate-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[96px]"
TAILWIND_SELECT = "block w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"


class TournamentCreationForm(forms.ModelForm):
    # Non-model field to capture the Game selection (used to filter formats client/server-side)
    game = forms.ModelChoiceField(
        queryset=Game.objects.all(),
        required=True,
        label="Game",
        widget=forms.Select(attrs={'class': TAILWIND_SELECT})
    )

    # Date field uses a native date input; widget class set to Tailwind utilities
    tournament_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': TAILWIND_INPUT}),
        help_text="The start date of the tournament."
    )

    class Meta:
        model = Tournament
        fields = [
            'tournament_format',
            'tournament_name',
            'description',
            'tournament_date',
            'prize_pool',
            'banner',
            'team_maximum_count',
        ]

        widgets = {
            'tournament_format': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'tournament_name': forms.TextInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'e.g., Summer Cup 2025'}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4, 'placeholder': 'Enter tournament rules, details, etc.'}),
            'prize_pool': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'e.g., 5000000'}),
            'banner': forms.URLInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'https://your-image-host.com/banner.png'}),
            'team_maximum_count': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'e.g., 16'}),
        }

        labels = {
            'prize_pool': 'Prize Pool (IDR)',
            'team_maximum_count': 'Maximum Team Entry',
            'banner': 'Banner Image URL',
        }

    def clean_tournament_date(self):
        date = self.cleaned_data.get('tournament_date')
        if date and date < timezone.localdate():
            raise forms.ValidationError("Tournament date cannot be in the past.")
        return date
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Loop through all fields and add Tailwind classes

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': (
                    'w-full rounded-lg border-gray-300 '
                    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 '
                    'px-3 py-2 text-gray-900 placeholder-gray-400 bg-white'
                )
            })

        # By default, don't expose all formats until a game is selected (JS will populate)
        # This improves UX and prevents showing irrelevant formats.
        self.fields['tournament_format'].queryset = TournamentFormat.objects.none()

        # If there's a posted 'game' value (POST request), restrict the format queryset accordingly
        if 'game' in self.data:
            try:
                game_id = self.data.get('game')
                if game_id:
                    self.fields['tournament_format'].queryset = TournamentFormat.objects.filter(game_id=game_id)
            except (ValueError, TypeError):
                self.fields['tournament_format'].queryset = TournamentFormat.objects.none()
        # If editing an existing Tournament instance, pre-populate formats for the instance's game
        elif self.instance and getattr(self.instance, 'tournament_format', None):
            tf = self.instance.tournament_format
            self.fields['tournament_format'].queryset = TournamentFormat.objects.filter(game=tf.game)
            self.initial['game'] = tf.game

    def clean(self):
        cleaned = super().clean()
        game = cleaned.get('game')
        tournament_format = cleaned.get('tournament_format')
        if tournament_format and game and tournament_format.game != game:
            self.add_error('tournament_format', 'Selected format does not belong to the chosen game.')
        return cleaned