from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Sorgu bos"}), 400

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
        
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    unique_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)

    # İŞTE SİHİRLİ KISIM BURASI:
    # YouTube'a "Ben sunucu değilim, Android telefonum" diyoruz.
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android']  # Android kılığına girdik!
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            final_file = ydl.prepare_filename(info)
            return send_file(final_file, as_attachment=True, download_name=f"{info['title']}.{info['ext']}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
