from rest_framework import serializers
from .models import GameAccount
from django.conf import settings


class GameAccountSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = GameAccount
        fields = ('id', 'user', 'game', 'ingame_name', 'active')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # import at runtime
        from tournaments.models import Game
        if 'game' in self.fields:
            self.fields['game'].queryset = Game.objects.all()

    def validate_ingame_name (self, value):
        return value.strip()