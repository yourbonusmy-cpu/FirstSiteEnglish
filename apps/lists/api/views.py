from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import (
    OuterRef,
    Exists,
    Subquery,
    IntegerField,
    F,
    ExpressionWrapper,
    Count,
)

from .serializers import SubtitleListSerializer
from ..models import UserSubtitleList, SubtitleList
from ...social.models import SubtitleListLike


class SubtitleListViewSet(viewsets.ModelViewSet):
    serializer_class = SubtitleListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = SubtitleList.objects.filter(owner=user)

        user_list_qs = UserSubtitleList.objects.filter(
            user=user,
            subtitle_list=OuterRef("pk"),
        )

        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"),
                    user=user,
                )
            ),
            user_quantity_learned_words=Subquery(
                user_list_qs.values("quantity_learned_words")[:1],
                output_field=IntegerField(),
            ),
            is_open_menu=Subquery(
                user_list_qs.values("is_open_menu")[:1],
            ),
            progress_percent=ExpressionWrapper(
                100 * F("quantity_learned_words") / F("quantity_words"),
                output_field=IntegerField(),
            ),
            likes_count=Count("likes"),
        ).order_by("-modified_time")

        return qs

    # 🔹 /api/lists/my/
    @action(detail=False, methods=["get"])
    def my(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # 🔹 like toggle
    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        obj = self.get_object()

        like, created = SubtitleListLike.objects.get_or_create(
            user=request.user, subtitle_list=obj
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return Response({"liked": liked, "likes_count": obj.likes.count()})

    # 🔹 toggle publish
    @action(detail=True, methods=["post"])
    def toggle_publish(self, request, pk=None):
        obj = self.get_object()
        obj.is_public = not obj.is_public
        obj.save()

        return Response({"is_public": obj.is_public})

    # 🔹 toggle menu
    @action(detail=True, methods=["post"])
    def toggle_menu(self, request, pk=None):
        user_list, _ = UserSubtitleList.objects.get_or_create(
            user=request.user, subtitle_list=self.get_object()
        )

        user_list.is_open_menu = request.data.get("is_open_menu", False)
        user_list.save()

        return Response({"is_open_menu": user_list.is_open_menu})

    # 🔹 update progress
    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        user_list = UserSubtitleList.objects.get(
            user=request.user, subtitle_list=self.get_object()
        )

        percent = int(
            100
            * user_list.quantity_learned_words
            / user_list.subtitle_list.quantity_words
        )

        return Response(
            {"percent": percent, "learned": user_list.quantity_learned_words}
        )
