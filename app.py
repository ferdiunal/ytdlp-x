from flask import Flask, request, abort, send_file
import os
import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip
import uuid
import json
import base64

app = Flask(__name__)

OUTPUT_DIR = 'output'

# Klasörü oluştur
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 'tmp' alt klasörünü oluştur
if not os.path.exists(os.path.join(OUTPUT_DIR, 'tmp')):
    os.makedirs(os.path.join(OUTPUT_DIR, 'tmp'))

def extract_youtube_info(info_dict):
    hostname = request.host
    scheme = request.scheme
    
    print('extract_youtube_info')
    video_formats = [
        fmt for fmt in info_dict.get('formats', [])
        if fmt.get('vcodec') != 'none' and fmt.get('acodec') == 'none'
    ]
    print(f"video_formats: {video_formats}")
    audio_formats = [
        fmt for fmt in info_dict.get('formats', [])
        if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none'
    ]
    print(f"audio_formats: {audio_formats}")
    
    video_formats.sort(key=lambda x: x.get('height') or 0, reverse=True)
    audio_formats.sort(key=lambda x: x.get('abr') or 0, reverse=True)

    print(f"video_formats: {video_formats}")
    print(f"audio_formats: {audio_formats}")
    print('all sorted')

    if not video_formats or not audio_formats:
        raise ValueError("No suitable video or audio format found")

    best_video = video_formats[0]
    best_audio = audio_formats[0]
    
    print(f"best_video: {best_video}")
    print(f"best_audio: {best_audio}")

    video_id = str(info_dict['id'])
    output_path = os.path.join(OUTPUT_DIR, f'{video_id}.mp4')

    ydl_opts = {
        'format': f"{best_video['format_id']}+{best_audio['format_id']}",
        'outtmpl': {'default': os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.%(ext)s')},
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download([info_dict['webpage_url']])
        if error_code != 0:
            raise ValueError(f"Failed to download video. Error code: {error_code}")

    # Birleştirilmiş dosyanın adını kontrol et
    merged_file = os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.mp4')
    
    if not os.path.exists(merged_file):
        raise FileNotFoundError(f"Merged video file not found: {merged_file}")

    # Birleştirilmiş dosyayı son çıktı konumuna taşı
    os.rename(merged_file, output_path)

    # Encode the video_id to make it URL-safe
    url_safe_video_id = base64.urlsafe_b64encode(video_id.encode()).decode().rstrip('=')

    return {
        'title': info_dict.get('title'),
        'video_id': f"{scheme}://{hostname}/stream/{url_safe_video_id}",
    }

def extract_tiktok_info(info_dict):
    print('extract_tiktok_info')
    mp4_formats = [
        fmt for fmt in info_dict.get('formats', [])
        if fmt.get('cookies') is None and fmt.get("width") >= 720
    ]
    mp4_formats.sort(key=lambda x: x.get('width'), reverse=True)
    return mp4_formats[0]["url"] if mp4_formats else None

def extract_instagram_info(info_dict):
    print('extract_instagram_info')
    hostname = request.host
    scheme = request.scheme

    video_formats = [
        fmt for fmt in info_dict.get('formats', [])
        if fmt.get('vcodec') != 'none' and fmt.get('acodec') == 'none'
    ]
    audio_formats = [
        fmt for fmt in info_dict.get('formats', [])
        if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none'
    ]

    video_formats.sort(key=lambda x: x.get('height') or 0, reverse=True)
    audio_formats.sort(key=lambda x: x.get('abr') or 0, reverse=True)

    if not video_formats or not audio_formats:
        raise ValueError("No suitable video or audio format found")

    best_video = video_formats[0]
    best_audio = audio_formats[0]

    video_id = str(info_dict['id'])
    output_path = os.path.join(OUTPUT_DIR, f'{video_id}.mp4')

    ydl_opts = {
        'format': f"{best_video['format_id']}+{best_audio['format_id']}",
        'outtmpl': {'default': os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.%(ext)s')},
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download([info_dict['webpage_url']])
        if error_code != 0:
            raise ValueError(f"Failed to download video. Error code: {error_code}")

    merged_file = os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.mp4')
    
    if not os.path.exists(merged_file):
        raise FileNotFoundError(f"Merged video file not found: {merged_file}")

    os.rename(merged_file, output_path)

    url_safe_video_id = base64.urlsafe_b64encode(video_id.encode()).decode().rstrip('=')

    return {
        'title': info_dict.get('title'),
        'video_id': f"{scheme}://{hostname}/stream/{url_safe_video_id}",
    }

def extract_video_info(url, cookieFileName):
    ydl_opts = {
        "format": "best",
        'noplaylist': True,
        "cookiefile": os.path.join(os.getcwd(), cookieFileName),
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        return info_dict

@app.route("/", methods=["GET"])
def main():
    print([os.getenv("PROXY"), os.getenv("AUTHORIZATION")]) 
    print([request.headers.get("authorization"), os.getenv("AUTHORIZATION")])
    
    if request.headers.get("authorization") != os.getenv("AUTHORIZATION"):
        abort(500)

    try:
        url = request.args.get('url')
        cookieFileName = "cookies/youtube.cookies.txt"
        
        if url.startswith("https://www.tiktok.com/@"):
            cookieFileName = "cookies/tiktok.cookies.txt"
            info_dict = extract_video_info(url, cookieFileName)
            video_url = extract_tiktok_info(info_dict)
        elif url.startswith("https://www.youtube.com"):
            info_dict = extract_video_info(url, cookieFileName)
            result = extract_youtube_info(info_dict)
            return {
                'caption': result['title'],
                'video_id': result['video_id']
            }
        elif url.startswith("https://www.instagram.com"):
            cookieFileName = "cookies/instagram.cookies.txt"
            info_dict = extract_video_info(url, cookieFileName)
            video_url = extract_instagram_info(info_dict)
        else:
            raise ValueError("Unsupported URL")
        
        if video_url is None:
            raise ValueError("No suitable video format found")
        
        return {
            'caption': info_dict.get('title'),
            'url': video_url
        }
    except Exception as e:
        print(e)
        abort(500)

@app.route("/stream/<video_id>", methods=["GET"])
def stream_video(video_id):
    # Decode the URL-safe video_id back to its original form
    original_video_id = base64.urlsafe_b64decode(video_id + '==').decode()
    
    video_path = os.path.join(OUTPUT_DIR, f'{original_video_id}.mp4')
    if not os.path.exists(video_path):
        abort(404)
    return send_file(video_path, mimetype='video/mp4')

if __name__ == "__main__":
    app.run()