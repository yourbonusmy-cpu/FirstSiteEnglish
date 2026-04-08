from rest_framework import serializers

from apps.lists.models import SubtitleList


class SubtitleListSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField(read_only=True)
    user_quantity_learned_words = serializers.IntegerField(read_only=True)
    is_open_menu = serializers.BooleanField(read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)

    background_image = serializers.SerializerMethodField()

    class Meta:
        model = SubtitleList
        fields = [
            "id",
            "name",
            "background_image",
            "background_color",
            "quantity_words",
            "is_public",
            "is_liked",
            "user_quantity_learned_words",
            "is_open_menu",
            "progress_percent",
            "likes_count",
        ]

    def get_background_image(self, obj):
        if obj.background_image:
            return obj.background_image.url
        return None
