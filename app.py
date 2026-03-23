from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import urllib.request
import json

app = Flask(__name__)
CORS(app)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Sorgu bos"}), 400

    # Arama kısmında engel yok, yt-dlp tıkır tıkır çalışır.
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = []
            for entry in search_results['entries']:
                duration_val = entry.get('duration')
                if duration_val:
                    try:
                        total_seconds = int(float(duration_val))
                        mins = total_seconds // 60
                        secs = total_seconds % 60
                        duration_str = f"{mins}:{secs:02d}"
                    except:
                        duration_str = "00:00"
                else:
                    duration_str = "00:00"

                results.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'thumbnail': entry['thumbnails'][-1]['url'] if entry.get('thumbnails') else '',
                    'duration': duration_str
                })
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def download():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "ID eksik"}), 400
        
    # İŞTE "DOĞRU DÜZGÜN" YÖNTEM:
    # yt-dlp indirmesini çöpe atıp, YouTube'a takılmayan Piped API'ye bağlanıyoruz.
    piped_url = f"https://pipedapi.kavin.rocks/streams/{video_id}"
    
    try:
        req = urllib.request.Request(piped_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        audio_url = None
        title = data.get('title', 'Sarki')
        safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip()
        
        # En iyi M4A ses dosyasını çekiyoruz
        for stream in data.get('audioStreams', []):
            if stream.get('format') == 'M4A':
                audio_url = stream.get('url')
                break
                
        if not audio_url and data.get('audioStreams'):
            audio_url = data['audioStreams'][0].get('url')
            
        if audio_url:
            # Sesi YouTube'dan gizlice alıp doğrudan telefonuna "indir" komutuyla yolluyoruz
            audio_req = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
            audio_response = urllib.request.urlopen(audio_req)
            
            def generate():
                while True:
                    chunk = audio_response.read(1024 * 1024) # 1 MB parçalar
                    if not chunk:
                        break
                    yield chunk

            return Response(
                generate(),
                content_type='audio/mp4',
                headers={
                    'Content-Disposition': f'attachment; filename="{safe_title}.m4a"'
                }
            )
        else:
            return jsonify({"error": "Ses dosyasi bulunamadi"}), 404
            
    except Exception as e:
        return jsonify({"error": f"API Hatasi: Baska bir sarki deneyin."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                    
