from rest_framework import serializers
from .models import GameAccount
from django.conf import settings


class GameAccountSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    game = serializers.PrimaryKeyRelatedField(queryset=None)

    class Meta:
        model = GameAccount
        fields = ('id', 'user', 'game', 'ingame_name', 'active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from tournaments.models import Game
        self.fields['game'].queryset = Game.objects.all()

    def validate_ingame_name (self, value):
        return value.strip()