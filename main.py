from flask import Flask
from flask import request, abort
import os

import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def main():
    print([os.getenv("PROXY"), os.getenv("AUTHORIZATION")]) 
    print([request.headers.get("authorization"), os.getenv("AUTHORIZATION")])
    if request.headers.get("authorization") != os.getenv("AUTHORIZATION"):
        abort(500)

    try:
        cookieFileName = "/tmp/youtube.cookies.txt"
        if(str(request.args.get('url')).startswith("https://www.tiktok.com/@")):
            cookieFileName = "/tmp/tiktok.cookies.txt"
        elif(str(request.args.get('url')).startswith("https://www.instagram.com")):
            cookieFileName = "/tmp/instagram.cookies.txt"
        url = request.args.get('url')
        ydl_opts = {
            "format": "best",
            'noplaylist': True,
            # "cookiefile": os.path.join(os.getcwd(), cookieFileName),
            "cookiefile": cookieFileName,
            "proxy": os.getenv("PROXY", "http://ztaijadv:a13qe39b7nm7@38.154.227.167:5868"),
            "nocheckcertificate": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            mp4_formats = [
                fmt for fmt in info_dict.get('formats', [])
                if(str(url).startswith("https://www.tiktok.com/@") and fmt.get('cookies') is None and fmt.get("width") >= 720 or str(url).startswith("https://www.youtube.com") and fmt.get('ext') == 'mp4' and fmt.get('protocol') == 'https' and fmt.get('width') >= 720 or str(url).startswith("https://www.instagram.com") and fmt.get('width') is not None and fmt.get("width") >= 720)
            ]

            mp4_formats.sort(key=lambda x: x.get('width'), reverse=True)
        
            return {
                'caption': info_dict.get('title'),
                'url': mp4_formats[0]["url"]
            }
    except Exception as e:
        print(e)
        abort(500)