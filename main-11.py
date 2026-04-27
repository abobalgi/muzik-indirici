import os
import sys
import time
import logging
import threading
import unicodedata
import re
import urllib.request
import tarfile
from urllib.parse import quote

# ─────────────────────────────────────────────────────────────
# LOGGING & PATH AYARLARI
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='[FluxMusic] %(levelname)s %(message)s')
logger = logging.getLogger("fluxmusic")

paths_to_add = [
    os.path.join(os.path.expanduser("~"), ".local", "bin"),
    os.path.join(sys.prefix, "bin"),
    os.path.dirname(sys.executable)
]
current_path = os.environ.get("PATH", "")
for p in paths_to_add:
    if os.path.exists(p) and p not in current_path:
        current_path = p + os.pathsep + current_path
os.environ["PATH"] = current_path

# ─────────────────────────────────────────────────────────────
# WARP & WIREPROXY OTOMATIK KURULUM MOTORU (PYTHONIC)
# ─────────────────────────────────────────────────────────────
def setup_and_start_warp():
    if not os.path.exists("wireproxy.conf"):
        logger.info("[WARP] Wispbyte uzerinde kurulum basliyor... (Saf Python ile indiriliyor)")
        
        try:
            # 1. WGCF indir ve çalıştırılabilir yap
            urllib.request.urlretrieve("https://github.com/ViRb3/wgcf/releases/download/v2.2.22/wgcf_2.2.22_linux_amd64", "wgcf")
            os.chmod("wgcf", 0o755)
            
            # 2. Kayıt ol ve profili oluştur
            os.system("./wgcf register --accept-tos")
            time.sleep(3)
            os.system("./wgcf generate")
            
            # 3. Dosyayı yeniden adlandır ve SOCKS5 portunu ekle
            if os.path.exists("wgcf-profile.conf"):
                os.system("cp wgcf-profile.conf wireproxy.conf")
                with open("wireproxy.conf", "a") as f:
                    f.write("\n[Socks5]\nBindAddress = 127.0.0.1:40000\n")
            else:
                logger.error("[WARP] wgcf config uretemedi! Cloudflare API engeli olabilir.")
                
            # 4. Wireproxy aracını indir ve arşivden çıkar
            urllib.request.urlretrieve("https://github.com/pufferffish/wireproxy/releases/download/v1.0.7/wireproxy_linux_amd64.tar.gz", "wireproxy.tar.gz")
            with tarfile.open("wireproxy.tar.gz", "r:gz") as tar:
                tar.extractall()
            os.chmod("wireproxy", 0o755)
            logger.info("[WARP] Kurulum tamamlandi, VIP bilet hazir!")
        except Exception as e:
            logger.error(f"[WARP] Kurulum sirasinda hata olustu: {e}")

    logger.info("[WARP] SOCKS5 Tuneli (Port 40000) arka planda baslatiliyor...")
    os.system("nohup ./wireproxy -c wireproxy.conf > wireproxy.log 2>&1 &")
    time.sleep(2)

setup_and_start_warp()

# ─────────────────────────────────────────────────────────────
# GEREKLİ KÜTÜPHANELER (WARP BAŞLADIKTAN SONRA)
# ─────────────────────────────────────────────────────────────
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from collections import defaultdict
import requests
import yt_dlp

# JS Motorunu (Signature Solver) aktif et
try:
    import yt_dlp_ejs
    logger.info("[FluxMusic] yt_dlp_ejs eklentisi aktif, JS imza motoru calisiyor.")
except ImportError:
    logger.warning("[FluxMusic] yt_dlp_ejs eklentisi bulunamadi, bazi videolar indirilemeyebilir.")

app = Flask(__name__)
# CORS: ALLOWED_ORIGINS ortam degiskenini ayarla (örn: "https://siteadin.com")
# Ayarlanmazsa gelistirme kolayligi için tüm kaynaklara acik kalir
_allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
CORS(app, origins=_allowed_origins.split(',') if _allowed_origins != '*' else '*')

# ─────────────────────────────────────────────────────────────
# BASIT IN-MEMORY RATE LIMITER (ek paket gerekmez)
# ─────────────────────────────────────────────────────────────
_rate_store = defaultdict(list)
_rate_lock  = threading.Lock()
RATE_WINDOW = 60  # saniye

RATE_LIMITS = {
    '/search':         15,   # dakikada 15 arama
    '/stream_audio':   40,   # dakikada 40 stream
    '/download':       10,   # dakikada 10 indirme
    '/download_video':  5,   # dakikada 5 klip
}

def check_rate(endpoint):
    ip  = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    key = f"{ip}:{endpoint}"
    now = time.time()
    limit = RATE_LIMITS.get(endpoint, 60)
    with _rate_lock:
        _rate_store[key] = [t for t in _rate_store[key] if now - t < RATE_WINDOW]
        if len(_rate_store[key]) >= limit:
            return False
        _rate_store[key].append(now)
    return True

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
WARP_PROXY = 'socks5h://127.0.0.1:40000'

_session = requests.Session()
_session.proxies.update({'http': WARP_PROXY, 'https': WARP_PROXY})

# ─────────────────────────────────────────────────────────────
# YT-DLP ANA AYARLARI
# ─────────────────────────────────────────────────────────────
SPOOF_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.youtube.com/'
}

YDL_BASE_OPTS = {
    'quiet': True,
    'no_warnings': True, # Konsolu kirleten can sıkıcı sarı uyarıları tamamen susturur
    'nocheckcertificate': True,
    'proxy': WARP_PROXY,
    'http_headers': SPOOF_HEADERS,
    # YouTube'un şu anki en büyük açığı olan 'android_vr' (Sanal Gerçeklik) istemcisi eklendi
    'extractor_args': {'youtube': {'player_client': ['android_vr', 'android', 'web']}}
}

# ─────────────────────────────────────────────────────────────
# CACHE VE YARDIMCI FONKSIYONLAR
# ─────────────────────────────────────────────────────────────
_audio_cache = {}
_search_cache = {}
CACHE_TTL = 3600

def format_duration(d):
    try:
        s = int(float(d))
        return f"{s//60}:{s%60:02d}"
    except:
        return "00:00"

def make_safe_filename(text):
    text = (text or "FluxMusic_Media")
    tr_map = {'ı':'i', 'İ':'I', 'ş':'s', 'Ş':'S', 'ğ':'g', 'Ğ':'G', 'ü':'u', 'Ü':'U', 'ö':'o', 'Ö':'O', 'ç':'c', 'Ç':'C'}
    for t, a in tr_map.items(): text = text.replace(t, a)
    text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode('ascii')
    return re.sub(r'[^\w\s-]','',text).strip() or "FluxMusic_Media"

def stream_response(r, chunk_size=65536):
    for chunk in r.iter_content(chunk_size=chunk_size):
        if chunk: yield chunk

# ─────────────────────────────────────────────────────────────
# YT-DLP CORE FONKSIYONLAR (ARAMA VE LINK ÇIKARMA)
# ─────────────────────────────────────────────────────────────
def yt_search(query, limit=80):
    cache_key = query.lower().strip()
    if cache_key in _search_cache and time.time() - _search_cache[cache_key]['time'] < 600:
        return _search_cache[cache_key]['data']

    opts = dict(YDL_BASE_OPTS)
    opts.update({'extract_flat': True, 'ignoreerrors': True})
    results = []
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            data = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            for entry in (data.get('entries') or []):
                if not entry: continue
                dur = entry.get('duration') or 0
                if 0 < dur <= 600:
                    thumbs = entry.get('thumbnails') or []
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'thumbnail': thumbs[-1]['url'] if thumbs else '',
                        'duration': format_duration(dur)
                    })
        except Exception as e:
            logger.error(f"Arama hatasi: {e}")

    if results:
        _search_cache[cache_key] = {'data': results, 'time': time.time()}
    return results

def get_best_audio_url(video_id):
    if video_id in _audio_cache and time.time() - _audio_cache[video_id]['time'] < CACHE_TTL:
        return _audio_cache[video_id]['url'], _audio_cache[video_id]['title']

    opts = dict(YDL_BASE_OPTS)
    # --- YENİ KURAL: Önce kesinlikle m4a formatını ara ---
    opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            if info and info.get('url'):
                url, title = info.get('url'), info.get('title', 'FluxMusic_Media')
                _audio_cache[video_id] = {'url': url, 'title': title, 'time': time.time()}
                return url, title
        except Exception as e:
            logger.error(f"Ses linki cikarma hatasi: {e}")
    
    return None, None

# ─────────────────────────────────────────────────────────────
# ROTALAR (API)
# ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ok", "system": "FluxMusic WARP Edition v1.3", "proxy_status": "Active"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"ok": True, "status": "WARP Active"})

@app.route('/prefetch', methods=['GET'])
def prefetch():
    video_id = request.args.get('id')
    if not video_id: return jsonify({"ok": False, "reason": "id eksik"}), 400
    threading.Thread(target=get_best_audio_url, args=(video_id,), daemon=True).start()
    return jsonify({"ok": True, "queued": True})

@app.route('/search', methods=['GET'])
def search():
    if not check_rate('/search'):
        return jsonify({"error": "Çok fazla istek, biraz bekle"}), 429
    query = request.args.get('q', '').strip()
    if not query: query = "Turkce hit sarkilar pop rap"
    return jsonify(yt_search(query))

@app.route('/stream_audio')
def stream_audio():
    if not check_rate('/stream_audio'):
        return "Çok fazla istek", 429
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400

    audio_url, title = get_best_audio_url(video_id)
    if not audio_url: return "Ses kaynagi bulunamadi (WARP veya YT engeli)", 500

    try:
        req_h = dict(SPOOF_HEADERS)
        if request.headers.get('Range'): req_h['Range'] = request.headers.get('Range')
        r = _session.get(audio_url, headers=req_h, stream=True, timeout=20)
        
        if r.status_code in (403, 404, 410):
            _audio_cache.pop(video_id, None)
            return "Ses kaynagi suresi dolmus, lutfen tekrar deneyin.", 500

        resp_headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': r.headers.get('Content-Type', 'audio/webm'),
            'X-Accel-Buffering': 'no',
            'Cache-Control': 'no-cache',
        }
        if 'Content-Range' in r.headers: resp_headers['Content-Range'] = r.headers['Content-Range']
        if 'Content-Length' in r.headers: resp_headers['Content-Length'] = r.headers['Content-Length']

        return Response(stream_with_context(stream_response(r)), status=r.status_code, headers=resp_headers)
    except Exception as e:
        logger.error(f"Stream hatasi: {e}")
        return "Stream baglantisi kurulamadi", 500

@app.route('/download', methods=['GET'])
def download():
    if not check_rate('/download'):
        return "Çok fazla istek", 429
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400

    audio_url, title = get_best_audio_url(video_id)
    if not audio_url: return "Ses kaynagi bulunamadi", 500

    safe_title = make_safe_filename(title)
    
    try:
        r = _session.get(audio_url, stream=True, timeout=30, headers=SPOOF_HEADERS)
        if r.status_code in (403, 404, 410):
            _audio_cache.pop(video_id, None)
            return "Ses kaynagi suresi dolmus, lutfen tekrar deneyin.", 500

        content_type = r.headers.get('Content-Type','')
        ext = 'webm' if 'webm' in content_type else 'm4a'
        encoded_name = quote(f"{safe_title}.{ext}")
        
        resp_headers = {
            'Content-Disposition': f'attachment; filename="{safe_title}.{ext}"; filename*=UTF-8\'\'{encoded_name}',
            'Content-Type': content_type or f'audio/{ext}',
        }
        if 'Content-Length' in r.headers: resp_headers['Content-Length'] = r.headers['Content-Length']

        return Response(stream_with_context(stream_response(r)), status=r.status_code, headers=resp_headers)
    except Exception as e:
        logger.error(f"Indirme hatasi: {e}")
        return "Indirme basarisiz", 500

@app.route('/download_video', methods=['GET'])
def download_video():
    if not check_rate('/download_video'):
        return "Çok fazla istek", 429
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400

    opts = dict(YDL_BASE_OPTS)
    # Diske yazmadan sadece URL al — ses+görüntü birleşik (muxed) MP4 seç
    opts['format'] = 'best[ext=mp4][height<=480]/best[ext=mp4]/bestvideo[ext=mp4][height<=480]'

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            if not info or not info.get('url'):
                return "Video kaynagi bulunamadi", 500

            video_url  = info['url']
            title      = info.get('title', 'FluxMusic_Video')
            ext        = info.get('ext', 'mp4')
            quality    = info.get('height', '')
            safe_title = make_safe_filename(title)
            encoded_name = quote(f"{safe_title}.{ext}")

            req_h = dict(SPOOF_HEADERS)
            if request.headers.get('Range'):
                req_h['Range'] = request.headers.get('Range')

            r = _session.get(video_url, headers=req_h, stream=True, timeout=20)

            resp_headers = {
                'Content-Disposition': f'attachment; filename="{safe_title}.{ext}"; filename*=UTF-8\'\'{encoded_name}',
                'Content-Type':        r.headers.get('Content-Type', f'video/{ext}'),
                'Accept-Ranges':       'bytes',
                'X-Accel-Buffering':   'no',
                'Cache-Control':       'no-cache',
            }
            if quality:
                resp_headers['X-Video-Quality'] = f'{quality}p'
            if 'Content-Length' in r.headers:
                resp_headers['Content-Length'] = r.headers['Content-Length']
            if 'Content-Range' in r.headers:
                resp_headers['Content-Range'] = r.headers['Content-Range']

            return Response(
                stream_with_context(stream_response(r)),
                status=r.status_code,
                headers=resp_headers
            )
    except Exception as e:
        logger.error(f"Video indirme hatasi: {e}")

    return "Video indirme basarisiz", 500

@app.route('/lyrics', methods=['GET'])
def get_lyrics():
    query = request.args.get('q')
    if not query: return jsonify({"error": "Sorgu bos"}), 400
    try:
        clean_q = re.sub(r'\(.*?\)|\[.*?\]','', query)
        clean_q = re.sub(r'(?i)(official|video|audio|lyrics|lyric|klip|yeni|hq|hd|4k|feat\.|ft\.|prod\.|by)', '', clean_q)
        clean_q = clean_q.replace('|','').replace('"','').replace("'",'').replace('-',' ').strip()
        
        res = requests.get(f"https://lrclib.net/api/search?q={clean_q}", timeout=5)
        data = res.json()
        if data: return jsonify({'lyrics': data[0].get('plainLyrics'), 'synced': data[0].get('syncedLyrics')})
        return jsonify({"error": "Bulunamadi"}), 404
    except:
        return jsonify({"error": "Hata"}), 500

# ─────────────────────────────────────────────────────────────
# SUNUCUYU BAŞLAT
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', os.environ.get('SERVER_PORT', 12186)))

    # WARP kontrolü: wireproxy.conf yoksa uyar
    if not os.path.exists("wireproxy.conf"):
        logger.warning("[WARP] wireproxy.conf bulunamadi! YouTube istekleri proxy'siz gidebilir.")

    # Sunucuyu uyku modundan koru (Wispbyte ücretsiz plan)
    def _keep_alive():
        time.sleep(30)  # ilk başlamayı bekle
        while True:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5)
                logger.info("[KeepAlive] Ping OK")
            except Exception as e:
                logger.warning(f"[KeepAlive] Ping basarisiz: {e}")
            time.sleep(240)  # 4 dakikada bir

    threading.Thread(target=_keep_alive, daemon=True).start()

    app.run(host='0.0.0.0', port=port, threaded=True)