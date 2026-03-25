import subprocess
import sys
import os
import threading

# SİSTEM AÇILIRKEN EN GÜNCEL MOTORLARI İNDİRİR (Günde 1 kez çalışır)
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

# 1. KADEME: TELEGRAM VIP LİSTESİ (SABİT)
VIP_PROXIES = [
    "socks5://103.153.63.223:1080", "socks5://202.62.62.113:1080", "socks5://203.189.150.44:1080",
    "socks5://68.71.251.134:4145", "socks5://94.158.49.82:3128", "socks5://184.178.172.23:4145",
    "socks5://213.35.110.67:10864", "socks5://72.214.108.67:4145", "socks5://202.65.127.194:1080",
    "socks5://82.200.235.134:19170", "socks5://184.181.217.220:4145", "socks5://98.188.47.150:4145",
    "socks5://24.249.199.4:4145", "socks5://119.148.61.241:22122", "socks5://98.170.57.249:4145",
    "socks5://203.189.154.80:1080", "socks5://185.176.94.75:1080", "socks5://192.252.216.81:4145",
    "socks5://68.71.247.130:4145", "socks5://138.199.25.13:3907", "socks5://103.189.63.149:53053",
    "socks5://68.1.210.189:4145", "socks5://98.181.137.80:4145", "socks5://98.175.31.195:4145",
    "socks5://192.111.130.5:17002"
]

# 2. KADEME: CANLI DOSYA OKUYUCU (Kullanıcı her indirme yaptığında anında klasörü tarar!)
def get_live_file_proxies():
    live_proxies = []
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        proxy_files = glob.glob(os.path.join(base_dir, '*[Pp]roxies*.txt'))
        
        for p_file in proxy_files:
            with open(p_file, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                for p in lines:
                    clean_p = p.strip()
                    formatted_p = f"http://{clean_p}"
                    if clean_p and formatted_p not in live_proxies:
                        live_proxies.append(formatted_p)
        return live_proxies
    except:
        return []

# 3. KADEME: İNTERNETTEN ÜCRETSİZ ÇEKİLENLER (Açılışta 1 kez çeker)
def get_free_proxies():
    try:
        res = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all", timeout=5)
        proxies = res.text.strip().split('\r\n')
        valid_proxies = [f"http://{p}" for p in proxies if p] 
        print(f"[PROXY] İnternetten {len(valid_proxies)} proxy çekildi!")
        return valid_proxies
    except:
        return []

DYNAMIC_PROXIES = get_free_proxies()

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

# ZIRHLI KILIFLAR
CLIENT_FALLBACKS = [
    {'youtube': {'client': ['ios']}},
    {'youtube': {'client': ['tv']}},
    {'youtube': {'client': ['android_vr']}}
]

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
    except: pass 

    if is_trend and len(results) > 0:
        random.shuffle(results)
        
    return jsonify(results)

@app.route('/stream_audio')
def stream_audio():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400
    
    # ANLIK DOSYA OKUMA İŞLEMİ BURADA YAPILIYOR!
    FILE_PROXIES = get_live_file_proxies()
    
    test_proxies = []
    if VIP_PROXIES: test_proxies.append(random.choice(VIP_PROXIES))
    if FILE_PROXIES: test_proxies.append(random.choice(FILE_PROXIES))
    if DYNAMIC_PROXIES: test_proxies.append(random.choice(DYNAMIC_PROXIES))
    test_proxies.append(None) 

    for current_proxy in test_proxies:
        for spoof in CLIENT_FALLBACKS:
            try:
                ydl_opts = {
                    'format': 'bestaudio/best', 
                    'quiet': True,
                    'nocheckcertificate': True,
                    'source_address': '0.0.0.0',
                    'extractor_args': spoof,
                    'socket_timeout': 8
                }
                
                if current_proxy:
                    ydl_opts['proxy'] = current_proxy
                
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
            except: continue 
            
    return "Stream basarisiz", 500

@app.route('/download', methods=['GET'])
def download():
    cleanup_old_files()
    video_id = request.args.get('id')
    dl_type = request.args.get('type', 'audio')
    if not video_id: return "ID eksik", 400

    unique_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)
    
    # ANLIK DOSYA OKUMA İŞLEMİ BURADA YAPILIYOR!
    FILE_PROXIES = get_live_file_proxies()
    
    test_proxies = []
    if VIP_PROXIES: test_proxies.append(random.choice(VIP_PROXIES))       
    if FILE_PROXIES: test_proxies.append(random.choice(FILE_PROXIES))     
    if DYNAMIC_PROXIES: test_proxies.append(random.choice(DYNAMIC_PROXIES)) 
    test_proxies.append(None)                                             

    for current_proxy in test_proxies:
        for spoof in CLIENT_FALLBACKS:
            ydl_opts = {
                'outtmpl': f'{output_path}.%(ext)s', 
                'quiet': True, 
                'noplaylist': True,
                'nocheckcertificate': True,
                'source_address': '0.0.0.0',
                'extractor_args': spoof,
                'socket_timeout': 8 
            }
            
            if current_proxy:
                ydl_opts['proxy'] = current_proxy
                print(f"İndirme deneniyor -> Proxy: {current_proxy} | Maske: {spoof['youtube']['client'][0]}")
            else:
                print(f"İndirme deneniyor -> Direkt Bağlantı | Maske: {spoof['youtube']['client'][0]}")
            
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
            except: continue 
            
    return "Indirme hatasi", 500

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


# =====================================================================
# YT-DLP GÜNCELLEMESİ İÇİN 24 SAATTE BİR RESTART
# =====================================================================
def auto_updater():
    print("[SİSTEM] YouTube algoritma güncellemelerine karşı 24 saatlik sayaç devrede.")
    time.sleep(86400) 
    print("[SİSTEM] 24 SAAT DOLDU! yt-dlp motorunu tazelemek için sistem yeniden başlatılıyor...")
    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])

if __name__ == '__main__':
    threading.Thread(target=auto_updater, daemon=True).start()
    app.run(host='0.0.0.0', port=9079)
    
