import os
import re
import random
import requests
import unicodedata
from urllib.parse import quote
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# =========================================================================
# 🛡️ MELEZ MOTOR (HYBRID ENGINE): API + DAHİLİ YEDEK SİSTEM
# =========================================================================
COBALT_APIS = [
    "https://api.cobalt.tools/api/json"
]

PIPED_APIS = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.lunar.icu",
    "https://pipedapi.syncpundit.io"
]

def make_safe_filename(text):
    text = text.replace('ı', 'i').replace('İ', 'I').replace('ş', 's').replace('Ş', 'S')\
               .replace('ğ', 'g').replace('Ğ', 'G').replace('ü', 'u').replace('Ü', 'U')\
               .replace('ö', 'o').replace('Ö', 'O').replace('ç', 'c').replace('Ç', 'C')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip()
    if not text: text = "FluxMusic_Media"
    return text

def format_duration(d):
    if d:
        try:
            s = int(float(d))
            return f"{s // 60}:{s % 60:02d}"
        except: return "00:00"
    return "00:00"

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
    except Exception as e: 
        print(f"[ARAMA HATASI]: {e}")

    if is_trend and len(results) > 0:
        random.shuffle(results)
        
    return jsonify(results)

def get_audio_url(video_id):
    # 1. AŞAMA: COBALT API (En Güçlü API)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {"url": f"https://www.youtube.com/watch?v={video_id}", "isAudioOnly": True, "aFormat": "mp3"}
    for api in COBALT_APIS:
        try:
            res = requests.post(api, json=payload, headers=headers, timeout=8)
            if res.status_code in [200, 202]:
                data = res.json()
                if data.get('url'):
                    print("[SİSTEM] Cobalt API ile link bulundu!")
                    return data['url'], "FluxMusic_Media"
        except Exception as e:
            print(f"[COBALT HATA] {api} -> {e}")

    # 2. AŞAMA: PIPED API HAVUZU
    for api in PIPED_APIS:
        try:
            res = requests.get(f"{api}/streams/{video_id}", timeout=8)
            if res.status_code == 200:
                data = res.json()
                streams = data.get('audioStreams', [])
                if streams:
                    streams.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                    print(f"[SİSTEM] Piped API ile link bulundu! ({api})")
                    return streams[0]['url'], data.get('title', 'FluxMusic_Media')
        except Exception as e:
            print(f"[PIPED HATA] {api} atlandı.")
            continue

    # 3. AŞAMA: DAHİLİ YEDEK MOTOR (yt-dlp iOS Maskesi)
    # Eğer dış dünyadaki tüm API'ler çökerse sistem pes etmez, çerezsiz iOS maskesiyle işi kendisi bitirir!
    print("[SİSTEM] Tüm API'ler çöktü! Dahili iOS Yedek Motoru devreye giriyor...")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'nocheckcertificate': True,
            'source_address': '0.0.0.0',
            'extractor_args': {'youtube': {'client': ['ios']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            if info and info.get('url'):
                return info['url'], info.get('title', 'FluxMusic_Media')
    except Exception as e:
        print(f"[DAHİLİ MOTOR HATASI] -> {e}")

    return None, None

@app.route('/stream_audio')
def stream_audio():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400
    
    audio_url, _ = get_audio_url(video_id)
    if not audio_url:
        return "Tüm sunucular dolu, lütfen birazdan tekrar dene.", 500

    try:
        req_headers = {}
        if request.headers.get('Range'): req_headers['Range'] = request.headers.get('Range')

        r = requests.get(audio_url, headers=req_headers, stream=True)
        
        resp_headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': 'audio/mpeg'
        }
        if 'Content-Range' in r.headers: resp_headers['Content-Range'] = r.headers['Content-Range']
        if 'Content-Length' in r.headers: resp_headers['Content-Length'] = r.headers['Content-Length']

        def generate():
            for chunk in r.iter_content(chunk_size=32768):
                if chunk: yield chunk

        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e: 
        return "Stream basarisiz", 500

@app.route('/download', methods=['GET'])
def download():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400

    audio_url, title = get_audio_url(video_id)
    if not audio_url:
        return "Tüm sunucular dolu, lütfen birazdan tekrar dene.", 500
        
    try:
        safe_title = make_safe_filename(title)
        r = requests.get(audio_url, stream=True)
        
        # Opera ve Safari'yi adam eden nükleer seçenek aynen korundu
        mime = "application/octet-stream"
        encoded_name = quote(f"{safe_title}.mp3")
        
        resp_headers = {
            'Content-Disposition': f'attachment; filename="{safe_title}.mp3"; filename*=UTF-8\'\'{encoded_name}',
            'Content-Type': mime
        }
        if 'Content-Length' in r.headers: 
            resp_headers['Content-Length'] = r.headers['Content-Length']

        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk: yield chunk

        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e: 
        return "Indirme hatasi", 500

@app.route('/lyrics', methods=['GET'])
def get_lyrics():
    query = request.args.get('q')
    if not query: return jsonify({"error": "Sorgu bos"}), 400
    try:
        clean_q = re.sub(r'\(.*?\)|\[.*?\]', '', query)
        clean_q = re.sub(r'(?i)(official|video|audio|lyrics|lyric|klip|yeni|hq|hd|4k|feat\.|ft\.|prod\.|by)', '', clean_q)
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
                    
