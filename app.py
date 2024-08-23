from flask import Flask
from flask import request, abort, send_file
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import yt_dlp
import base64

load_dotenv()

OUTPUT_DIR = 'output'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if not os.path.exists(os.path.join(OUTPUT_DIR, 'tmp')):
    os.makedirs(os.path.join(OUTPUT_DIR, 'tmp'))

def is_url(target: str):
    parsed_url = urlparse(request.args.get('url'))
    return parsed_url.netloc in [f"www.{target}", target]

app = Flask(__name__)

@app.route("/s/<video_id>", methods=["GET"])
def stream(video_id):    
    video_id = base64.urlsafe_b64decode(video_id + "==").decode()
    video_path = os.path.join(OUTPUT_DIR, f'{video_id}.mp4')
    if not os.path.exists(video_path):
        abort(404)
    return send_file(video_path)

@app.route("/", methods=["GET"])
def main():
    # if not request.headers.get("authorization") or not request.args.get('url'):
    #     abort(500)
    # token = str(request.headers.get("authorization")).split("Bearer ")[1]
    # if token != os.getenv("AUTHORIZATION"):
    #     abort(500)

    if is_url('youtube.com'):
        return downloadAndStream("yt", "youtube.cookies.txt")
    
    if is_url('instagram.com'):
        return downloadAndStream("in", "instagram.cookies.txt")
    
    if is_url('tiktok.com'):
        return downloadAndStream("tt", "tiktok.cookies.txt")

def downloadAndStream(alias:str, cookieFileName:str):
    url = request.args.get('url')
    scheme = request.scheme
    hostname = request.host

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        'noplaylist': True,
        'merge_output_format': 'mp4',
        # "cookiefile": os.path.join(os.getcwd(), cookieFileName),
        "nocheckcertificate": True,
        "ffmpeg_location": os.getenv("FFMPEG_PATH"),
        "http_headers": {
            "User-Agent": os.getenv("USER_AGENT"),
        },
    }
    
    if alias != 'yt':
        ydl_opts["cookiefile"] = os.path.join(os.getcwd(), cookieFileName)
    else:
        ydl_opts["username"] = "oauth2"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_id = f"{alias}-{info_dict.get('id')}"
        output_path = os.path.join(OUTPUT_DIR, f'{video_id}.mp4')

        ydl_opts["format"] = info_dict.get('format_id')
        ydl_opts["outtmpl"] = {'default': os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.%(ext)s')}
        ydl_opts["merge_output_format"] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download(info_dict['webpage_url'])
            if error_code != 0:
                raise ValueError(f"Failed to download video. Error code: {error_code}")

            merged_file = os.path.join(OUTPUT_DIR + '/tmp', f'{video_id}.mp4')
            
            if not os.path.exists(merged_file):
                raise FileNotFoundError(f"Merged video file not found: {merged_file}")

            os.rename(merged_file, output_path)

            url_safe_video_id = base64.urlsafe_b64encode(video_id.encode()).decode().rstrip('=')

            return {
                'caption': info_dict.get('description') or info_dict.get('title'),
                'url': f"{scheme}://{hostname}/s/{url_safe_video_id}",
            }
