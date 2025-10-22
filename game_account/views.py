from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import GameAccount
from .serializers import GameAccountSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # read-only allowed to any authenticated
        if request.method in permissions.SAFE_METHODS:
            return True
        # must be authenticated and the owner
        return request.user.is_authenticated and obj.user == request.user


class GameAccountViewSet(viewsets.ModelViewSet):
    queryset = GameAccount.objects.select_related('game', 'user').all()
    serializer_class = GameAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_permissions(self):
        # allow anonymous read access for safe methods
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        # require auth for unsafe methods (create, destroy, etc.)
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        # public list filtered by game (used by widget)
        if self.action == 'list':
            # expose filter by game parameter for the game-filtered list widget.
            game_id = self.request.query_params.get('game')
            if game_id:
                return self.queryset.filter(game__id=game_id, active=True)
            # return current user's accounts (private list)
            if self.request.user.is_authenticated:
                return self.queryset.filter(user=self.request.user)
            # if anonymous return empty list
            return self.queryset.none()
        return self.queryset
   
    def create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # soft-delete, atau nanti hard delete tergantung dengan logika user_account yang belum diimplementasi
        obj = self.get_object()
        if obj.user != request.user and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        obj.active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def select_widget(self, request):
        # API endpoint for floating widget, returns active accounts for the current user, can be filtered by game id
        game_id = request.query_params.get('game')
        qs = GameAccount.objects.filter(user=request.user, active=True)
        if game_id:
            # publicly readable list of active accounts
            qs = GameAccount.objects.filter(game__id=game_id, active=True)
        else:
            # only the authenticated user's accounts
            if not request.user.is_authenticated:
                return Response([], status=200)
        qs = GameAccount.objects.filter(user=request.user, active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
