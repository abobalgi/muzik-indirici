import subprocess
import sys
import os

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", "https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "curl-cffi"])
except:
    pass

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import uuid
import glob
import time
import requests
import re
import unicodedata
import random

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def cleanup_old_files():
    now = time.time()
    for f in os.listdir(DOWNLOAD_FOLDER):
        p = os.path.join(DOWNLOAD_FOLDER, f)
        if os.path.isfile(p) and os.stat(p).st_mtime < now - 300:
            try: os.remove(p)
            except: pass

def format_duration(d):
    if d:
        try:
            s = int(float(d))
            return f"{s // 60}:{s % 60:02d}"
        except: return "00:00"
    return "00:00"

def make_safe_filename(text):
    text = text.replace('ı', 'i').replace('İ', 'I').replace('ş', 's').replace('Ş', 'S')\
               .replace('ğ', 'g').replace('Ğ', 'G').replace('ü', 'u').replace('Ü', 'U')\
               .replace('ö', 'o').replace('Ö', 'O').replace('ç', 'c').replace('Ç', 'C')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip()
    if not text: text = "FluxMusic_Media"
    return text

# Sadece iOS kılıfı bırakıldı (YouTube iPhone'lara şifre sormaz)
YT_CLIENT_SPOOF = {
    'youtube': {
        'client': ['ios', 'tv']
    }
}

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    is_trend = not query
    
    search_query = f"ytsearch80:{query}" if not is_trend else "ytsearch80:Türkçe hit şarkılar pop rap"
    
    ydl_opts = {
        'format': 'bestaudio/best', 
        'quiet': True, 
        'extract_flat': True,
        'ignoreerrors': True,
        'source_address': '0.0.0.0'
    }
    
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(search_query, download=False)
            for entry in data.get('entries', []):
                if entry:
                    dur = entry.get('duration') or 0
                    if 0 < dur <= 600:
                        results.append({
                            'id': entry.get('id'), 
                            'title': entry.get('title'),
                            'thumbnail': entry.get('thumbnails')[-1]['url'] if entry.get('thumbnails') else '',
                            'duration': format_duration(dur)
                        })
    except BaseException as e: 
        print(f"ARAMA HATASI: {e}")

    if is_trend and len(results) > 0:
        random.shuffle(results)
        
    return jsonify(results)

@app.route('/stream_audio')
def stream_audio():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400
    try:
        ydl_opts = {
            'format': 'bestaudio/best', 
            'quiet': False,
            'nocheckcertificate': True,
            'source_address': '0.0.0.0',
            'extractor_args': YT_CLIENT_SPOOF
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            audio_url = info['url']
            
            req_headers = {}
            if request.headers.get('Range'): req_headers['Range'] = request.headers.get('Range')

            r = requests.get(audio_url, headers=req_headers, stream=True)
            
            resp_headers = {
                'Accept-Ranges': 'bytes',
                'Content-Type': r.headers.get('Content-Type', 'audio/mpeg')
            }
            if 'Content-Range' in r.headers: resp_headers['Content-Range'] = r.headers['Content-Range']
            if 'Content-Length' in r.headers: resp_headers['Content-Length'] = r.headers['Content-Length']

            def generate():
                for chunk in r.iter_content(chunk_size=32768):
                    if chunk: yield chunk

            return Response(generate(), status=r.status_code, headers=resp_headers)
    except BaseException as e: 
        print(f"STREAM HATASI: {e}")
        return str(e), 500

@app.route('/download', methods=['GET'])
def download():
    cleanup_old_files()
    video_id = request.args.get('id')
    dl_type = request.args.get('type', 'audio')
    if not video_id: return "ID eksik", 400

    unique_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)
    ydl_opts = {
        'outtmpl': f'{output_path}.%(ext)s', 
        'quiet': False, # Gizli hataları görmek için False yaptık!
        'noplaylist': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0',
        'extractor_args': YT_CLIENT_SPOOF
    }
    
    if dl_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        ydl_opts['format'] = 'best[height<=480][ext=mp4]/bestvideo[height<=480]+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            safe_title = make_safe_filename(info.get('title', 'FluxMusic_Media'))
            downloaded = [f for f in glob.glob(f"{output_path}.*") if not f.endswith(('.part', '.ytdl'))]
            
            if downloaded:
                final_file = downloaded[0]
                ext = final_file.split('.')[-1]
                mime = "audio/mpeg" if ext == "mp3" else "video/mp4"
                with open(final_file, 'rb') as f: file_data = f.read()
                try: os.remove(final_file)
                except: pass
                return Response(file_data, mimetype=mime, headers={
                    'Content-Disposition': f'attachment; filename="{safe_title}.{ext}"'
                })
            else: 
                print("Dosya indirilemedi, liste boş!")
                return "Dosya hatasi", 500
    except BaseException as e: 
        print(f"İNDİRME HATASI: {e}") # İşte o gizli sorunu bu satır ifşa edecek!
        return str(e), 500

@app.route('/lyrics', methods=['GET'])
def get_lyrics():
    query = request.args.get('q')
    if not query: return jsonify({"error": "Sorgu bos"}), 400
    try:
        clean_q = re.sub(r'\(.*?\)|\[.*?\]', '', query)
        clean_q = re.sub(r'(?i)(official|video|audio|lyrics|lyric|klip|yeni|hq|hd|4k|feat\.|ft\.)', '', clean_q)
        clean_q = clean_q.replace('|', '').replace('"', '').replace("'", "").replace('-', ' ').strip()
        res = requests.get(f"https://lrclib.net/api/search?q={clean_q}", timeout=5)
        data = res.json()
        if data and len(data) > 0:
            return jsonify({
                "lyrics": data[0].get('plainLyrics'),
                "synced": data[0].get('syncedLyrics')
            })
        return jsonify({"error": "Bulunamadi"}), 404
    except: return jsonify({"error": "Hata"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9079)
            
