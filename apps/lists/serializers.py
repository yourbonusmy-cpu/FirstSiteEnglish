from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from django.db.models import (
    OuterRef,
    Subquery,
    Exists,
    F,
    IntegerField,
    ExpressionWrapper,
    Value,
)
from django.db.models.functions import Coalesce
from .models import SubtitleList, UserSubtitleList
from ..social.models import SubtitleListLike


# Сериализатор
class SubtitleListSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField(read_only=True)
    user_quantity_learned_words = serializers.IntegerField(read_only=True)
    is_open_menu = serializers.BooleanField(read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = SubtitleList
        fields = (
            "id",
            "name",
            "version",
            "is_hide",
            "is_public",
            "owner",
            "background_image",
            "background_color",
            "quantity_words",
            "quantity_learned_words",
            "is_liked",
            "user_quantity_learned_words",
            "is_open_menu",
            "progress_percent",
        )


# ViewSet с объединёнными аннотациями
class UserSubtitleListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubtitleListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Подзапрос для проверки лайка
        like_subquery = SubtitleListLike.objects.filter(
            subtitle_list=OuterRef("pk"), user=user
        )

        # Подзапрос для UserSubtitleList
        user_list_subquery = UserSubtitleList.objects.filter(
            user=user, subtitle_list=OuterRef("pk")
        )

        # Основной queryset с аннотациями
        qs = (
            SubtitleList.objects.filter(owner=user)
            .select_related("owner")
            .order_by("-modified_time")
            .annotate(
                is_liked=Exists(like_subquery),
                user_quantity_learned_words=Coalesce(
                    Subquery(user_list_subquery.values("quantity_learned_words")[:1]),
                    Value(0),
                ),
                is_open_menu=Coalesce(
                    Subquery(user_list_subquery.values("is_open_menu")[:1]),
                    Value(False),
                ),
                progress_percent=ExpressionWrapper(
                    100
                    * Coalesce(
                        Subquery(
                            user_list_subquery.values("quantity_learned_words")[:1]
                        ),
                        Value(0),
                    )
                    / Coalesce(F("quantity_words"), Value(1)),
                    output_field=IntegerField(),
                ),
            )
        )
        return qs
