from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import random

app = Flask(__name__)
CORS(app)

# =========================================================================
# 🎼 ORKESTRA ŞEFİ: 6 KİŞİLİK ÖZEL HAREKAT TİMİNİ YÖNETEN ANA BEYİN
# =========================================================================
KLONLAR = [
    "http://217.154.94.16:9056",
    "http://85.215.229.230:9373",
    "http://212.132.99.151:9358",
    "http://217.154.94.16:9349",
    "http://85.215.229.230:9375",
    "http://212.227.7.153:9079"
]

@app.route('/', methods=['GET'])
def index():
    return "Orkestra Şefi Aktif! 6 İndirme Motoru Emre Amade... 🛡️🚀"

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    
    # Yükü dengelemek için 6 sunucuyu her istekte rastgele sıraya diziyoruz
    aktif_klonlar = random.sample(KLONLAR, len(KLONLAR))
    
    for klon in aktif_klonlar:
        try:
            res = requests.get(f"{klon}/search?q={query}", timeout=15)
            if res.status_code == 200:
                return jsonify(res.json())
        except Exception as e:
            print(f"[ŞEF UYARISI] {klon} arama yanıtı vermedi. Diğerine geçiliyor...")
            continue
            
    return jsonify({"error": "Tüm sunucular şu an meşgul, lütfen birazdan tekrar dene."}), 500

@app.route('/stream_audio')
def stream_audio():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400
    
    aktif_klonlar = random.sample(KLONLAR, len(KLONLAR))
    
    for klon in aktif_klonlar:
        try:
            req_headers = {}
            if request.headers.get('Range'): req_headers['Range'] = request.headers.get('Range')
            
            # Dinleme isteğini rastgele bir klona gönder
            r = requests.get(f"{klon}/stream_audio?id={video_id}", headers=req_headers, stream=True, timeout=20)
            
            if r.status_code in [200, 206]:
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
            else:
                print(f"[ŞEF UYARISI] {klon} stream veremedi (Kod: {r.status_code}). Sıradakine geçiliyor...")
        except Exception as e:
            continue
            
    return "Tüm sunucular meşgul", 500

@app.route('/download', methods=['GET'])
def download():
    video_id = request.args.get('id')
    if not video_id: return "ID eksik", 400

    aktif_klonlar = random.sample(KLONLAR, len(KLONLAR))
    
    for klon in aktif_klonlar:
        try:
            # İndirme isteğini rastgele bir işçiye pasla
            r = requests.get(f"{klon}/download?id={video_id}", stream=True, timeout=30)
            
            if r.status_code == 200:
                # Klonun oluşturduğu o özel (Opera'yı ve iOS'u çözen) başlıkları aynen kullanıcıya pasla
                resp_headers = {
                    'Content-Disposition': r.headers.get('Content-Disposition', f'attachment; filename="FluxMusic_{video_id}.mp3"'),
                    'Content-Type': r.headers.get('Content-Type', 'application/octet-stream')
                }
                if 'Content-Length' in r.headers: 
                    resp_headers['Content-Length'] = r.headers['Content-Length']

                def generate():
                    # 64KB'lık dev paketlerle kullanıcıya jet gibi akıt
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk: yield chunk

                return Response(generate(), status=r.status_code, headers=resp_headers)
            else:
                print(f"[ŞEF UYARISI] {klon} indirmeyi reddetti (Kod: {r.status_code}). Sıradakine geçiliyor...")
        except Exception as e:
            continue
            
    return "Tüm sunucular meşgul", 500

@app.route('/lyrics', methods=['GET'])
def lyrics():
    query = request.args.get('q', '')
    aktif_klonlar = random.sample(KLONLAR, len(KLONLAR))
    
    for klon in aktif_klonlar:
        try:
            res = requests.get(f"{klon}/lyrics?q={query}", timeout=10)
            if res.status_code == 200:
                return jsonify(res.json())
        except Exception:
            continue
            
    return jsonify({"error": "Şarkı sözü bulunamadı"}), 404

if __name__ == '__main__':
    # Render'ın kendi portunu bulması için
    import os
    port = int(os.environ.get('PORT', 9079))
    app.run(host='0.0.0.0', port=port)
    
