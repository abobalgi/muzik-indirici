from flask import Flask, request, send_file, jsonify, redirect
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Sorgu bos"}), 400

    # Arama için daha hafif ve engellenmesi zor ayarlar
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = []
            for entry in search_results['entries']:
                duration_val = entry.get('duration')
                if duration_val:
                    total_seconds = int(float(duration_val))
                    mins = total_seconds // 60
                    secs = total_seconds % 60
                    duration_str = f"{mins}:{secs:02d}"
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
        return "ID eksik", 400
    
    # Render IP engeline takılmamak için kullanıcıyı 
    # güvenli ve hızlı bir indirme servisine yönlendiriyoz.
    # Bu yöntem sunucunu yormaz ve bot kontrolüne takılmaz!
    download_url = f"https://api.vevioz.com/@download/128-mp3/{video_id}"
    return redirect(download_url)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
