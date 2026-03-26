import os
import re
import random
import requests
import unicodedata
from urllib.parse import quote
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp  # Sadece sivil ve ban riski olmayan arama işlemi için tutuyoruz

app = Flask(__name__)
CORS(app)

# =========================================================================
# 🛡️ YENİ ÇAĞ: API HAVUZU (ÇEREZ YOK, BAN YOK, BEKLEME YOK!)
# Bu sunucular dünya çapındaki açık kaynak gönüllülerine aittir.
# YouTube'un bot korumasıyla onlar savaşır, biz sadece MP3'ü alır çıkarız!
# =========================================================================
API_POOL = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.smnz.de",
    "https://pi.pivp.en",
    "https://piped-api.garudalinux.org"
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
    
    # Arama yapmak asla ban yedirmez, bu yüzden yt-dlp'yi burada en sivil ayarlarla kullanıyoruz.
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
                    if 0 < dur <= 600: # 10 dakikadan uzun videoları filtrele
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

def get_audio_url_from_api(video_id):
    """API Havuzunda sırayla dolaşır, çalışan ilk sunucudan en kaliteli ses linkini çalar!"""
    for api in API_POOL:
        try:
            res = requests.get(f"{api}/streams/{video_id}", timeout=7)
            if res.status_code == 200:
                data = res.json()
                audio_streams = data.get('audioStreams', [])
                if audio_streams:
                    # Sesleri kaliteye (bitrate) göre en yüksekten en düşüğe sırala
                    audio_streams.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                    return audio_streams[0]['url'], data.get('title', 'FluxMusic_Media')
        except Exception as e:
            print(f"[API ATLANDI] {api} sunucusu yanıt vermedi, diğerine geçiliyor...")
            continue
    return None, None

@app.route('/stream_audio')
def stream_audio():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400
    
    audio_url, _ = get_audio_url_from_api(video_id)
    if not audio_url:
        return "Tüm API sunucuları dolu, lütfen birazdan tekrar dene.", 500

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

    # DOĞRUDAN API'DEN ŞARKIYI BULUYORUZ (DİSK KULLANIMI SIFIR!)
    audio_url, title = get_audio_url_from_api(video_id)
    if not audio_url:
        return "Tüm API sunucuları dolu, lütfen birazdan tekrar dene.", 500
        
    try:
        safe_title = make_safe_filename(title)
        
        # Sesi kendi sunucumuza indirmeden, anlık olarak kullanıcıya paslıyoruz!
        r = requests.get(audio_url, stream=True)
        
        # Tüm tarayıcıları (Opera dâhil) adam eden nükleer seçenek
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
        # Şarkı sözü araması için isimleri tertemiz yapan o efsanevi filtre
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
                
