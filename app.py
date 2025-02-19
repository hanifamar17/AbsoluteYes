from flask import Flask, render_template, request, jsonify, url_for
import uuid
import requests
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_URL = f"https://api.github.com/gists/{GIST_ID}"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_gist_data():
    """Mengambil data dari Gist"""
    response = requests.get(GIST_URL, headers=HEADERS)
    
    if response.status_code == 200:
        gist_content = response.json()["files"]["responses.json"]["content"]
        return json.loads(gist_content)
    else:
        return []

def update_gist(data):
    """Mengupdate responses.json di Gist"""
    existing_data = get_gist_data()
    existing_data.append(data)  # Tambahkan data baru
    
    response = requests.patch(GIST_URL, headers=HEADERS, json={
        "files": {
            "responses.json": {
                "content": json.dumps(existing_data, indent=4)
            }
        }
    })
    
    return response.status_code == 200

@app.route('/submit', methods=['POST'])
def submit():
    try:
        print(f"Content-Type diterima: {request.content_type}")  # Debugging

        # Cek apakah request berupa JSON atau form-data
        if request.content_type == "application/json":
            req_data = request.get_json()
        elif request.content_type.startswith("multipart/form-data"):
            req_data = request.form.to_dict()
        else:
            return jsonify({'status': 'error', 'message': 'Unsupported Content-Type'}), 415

        if not req_data:
            return jsonify({'status': 'error', 'message': 'Invalid or empty data'}), 400

        # Buat ID unik
        unique_id = str(uuid.uuid4())

        data = {
            'id': unique_id,
            'question': req_data.get('question', ''),
            'description': req_data.get('description', ''),
            'answer_yes': req_data.get('answer_yes', 'Yes'),
            'answer_no': req_data.get('answer_no', 'No')
        }

        print(f"Data yang diterima: {data}")  # Debugging

        # Simpan ke Gist
        if not update_gist(data):
            return jsonify({'status': 'error', 'message': 'Failed to update Gist'}), 500

        # Kembalikan URL untuk melihat pertanyaan
        view_url = url_for('view_response', id=unique_id, _external=True)

        return jsonify({'status': 'success', 'id': unique_id, 'view_url': view_url})

    except Exception as e:
        print(f"Error in /submit: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/view/<id>', methods=['GET'])
def view_response(id):
    try:
        responses = get_gist_data()
        response = next((resp for resp in responses if resp['id'] == id), None)
        
        if response:
            return render_template('view.html', response=response)
        return jsonify({'status': 'error', 'message': 'Response not found'}), 404
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/history', methods=['GET'])
def history():
    try:
        # Ambil semua data dari Gist
        responses = get_gist_data()[::-1]  # Urutkan dari terbaru ke terlama

        # Ambil parameter limit dari request, default ke 10
        limit = request.args.get('limit', default=10, type=int)

        # Ambil hanya sejumlah limit (misalnya 10 data terbaru)
        latest_responses = responses[:limit]

        return jsonify({
            "status": "success",
            "data": latest_responses,
            "total": len(latest_responses)
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

#if __name__ == '__main__':
#    port = int(os.getenv("PORT", 5000))  # Pakai PORT dari env (Vercel)
#    app.run(host='0.0.0.0', port=port)
