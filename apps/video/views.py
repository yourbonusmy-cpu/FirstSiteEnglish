from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import os
from django.http import FileResponse, Http404
from django.conf import settings
from pathlib import Path


def stream_video(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, "videos", "test", filename)

    if not os.path.exists(file_path):
        raise Http404

    file_size = os.path.getsize(file_path)

    range_header = request.headers.get("Range", "").strip()
    if range_header:
        range_match = range_header.split("=")[1]
        start_str, end_str = range_match.split("-")

        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
        length = end - start + 1

        f = open(file_path, "rb")
        f.seek(start)

        response = FileResponse(f, status=206, content_type="video/mp4")
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"

        return response

    return FileResponse(open(file_path, "rb"), content_type="video/mp4")


# Create your views here.
@login_required
def video_player(request):
    return render(
        request,
        "video/player.html",
        {
            "subtitle_json": "/media/subtitles/test/video_name.tokens.json",
        },
    )


@login_required
def video_test(request):
    return render(request, "video/player_test.html")


# def youtube_download(request):
#     """
#     Страница:
#     - ввод ссылки
#     - показ доступных качеств
#     """
#     context = {}
#
#     if request.method == "POST":
#         url = request.POST.get("youtube_url")
#
#         ydl_opts = {
#             "quiet": True,
#             "force_ipv4": True,
#         }
#
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=False)
#
#         formats = []
#         for f in info["formats"]:
#             if f.get("vcodec") != "none" and f.get("filesize"):
#                 formats.append(
#                     {
#                         "format_id": f["format_id"],
#                         "ext": f["ext"],
#                         "resolution": f.get("resolution") or f"{f.get('height')}p",
#                         "filesize": round(f["filesize"] / 1024 / 1024, 1),
#                     }
#                 )
#
#         context = {
#             "title": info["title"],
#             "url": url,
#             "formats": formats,
#         }
#
#     return render(request, "video/youtube_download.html", context)


# def youtube_download_file(request):
#     """
#     Физическое скачивание видео
#     """
#     url = request.GET.get("url")
#     format_id = request.GET.get("format_id")
#
#     if not url or not format_id:
#         raise Http404
#
#     output_dir = Path(settings.MEDIA_ROOT) / "youtube"
#     output_dir.mkdir(parents=True, exist_ok=True)
#
#     ydl_opts = {
#         "format": format_id,
#         "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
#         "quiet": True,
#         "force_ipv4": True,
#     }
#
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         file_path = ydl.prepare_filename(info)
#
#     if not os.path.exists(file_path):
#         raise Http404
#
#     return FileResponse(
#         open(file_path, "rb"),
#         as_attachment=True,
#         filename=os.path.basename(file_path),
#     )
