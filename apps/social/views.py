from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from apps.lists.models import SubtitleList
from apps.social.models import SubtitleListLike


@login_required
@require_POST
def toggle_like(request, pk):
    """
    Переключает лайк у списка и рассылает обновление
    через Redis + Channels
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        pk=pk,
        is_public=True
    )

    user = request.user

    # Проверяем, есть ли лайк
    like = SubtitleListLike.objects.filter(
        user=user,
        subtitle_list=subtitle_list
    ).first()

    if like:
        like.delete()
        liked = False
    else:
        SubtitleListLike.objects.create(
            user=user,
            subtitle_list=subtitle_list
        )
        liked = True

    likes_count = SubtitleListLike.objects.filter(
        subtitle_list=subtitle_list
    ).count()

    # Рассылка события всем клиентам
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "likes_updates",
        {
            "type": "like_update",
            "list_id": subtitle_list.id,
            "likes_count": likes_count,
        }
    )

    return JsonResponse({
        "liked": liked,
        "likes_count": likes_count,
    })


# @login_required
# @require_POST
# def toggle_like(request, pk):
#     subtitle_list = get_object_or_404(
#         SubtitleList,
#         pk=pk,
#         is_public=True
#     )
#
#     like, created = SubtitleListLike.objects.get_or_create(
#         user=request.user,
#         subtitle_list=subtitle_list
#     )
#
#     if not created:
#         like.delete()
#         liked = False
#     else:
#         liked = True
#
#     return JsonResponse({
#         "liked": liked,
#         "likes_count": subtitle_list.likes.count()
#     })
