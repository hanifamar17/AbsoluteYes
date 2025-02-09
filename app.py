from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import uuid
import os

app = Flask(__name__)

# Endpoint untuk menyimpan pertanyaan
@app.route('/submit', methods=['POST'])
def submit():
    try:
        #print("Received Data:", request.form)  # Debugging

        # Validasi input
        if 'question' not in request.form:
            return jsonify({'status': 'error', 'message': 'Field question is missing'}), 400

        # Ambil data dari form
        data = {
            'id': str(uuid.uuid4()),  # Gunakan UUID untuk ID unik
            'question': request.form['question'],
            'description': request.form.get('description', ''),
            'answer_yes': request.form.get('answer_yes', 'Yes'),
            'answer_no': request.form.get('answer_no', 'No')
        }

        # Debug sebelum menyimpan
        print("Data to be saved:", data)

        # Baca data lama
        responses = get_all_responses()
        #print("Existing Data:", responses)  # Debugging

        # Tambahkan data baru
        responses.append(data)

        # Simpan ke JSON
        with open('responses.json', 'w') as f:
            json.dump(responses, f, indent=4)

        print("Data saved successfully!")  # Debugging

        return jsonify({'status': 'success', 'id': data['id'], 'link': url_for('view_response', id=data['id'], _external=True)})

    except Exception as e:
        print("Error:", str(e))  # Debugging error
        return jsonify({'status': 'error', 'message': str(e)}), 400
    
# Fungsi untuk mendapatkan semua data
def get_all_responses():
    try:
        if not os.path.exists('responses.json'):
            return []  # Jika file tidak ada, kembalikan array kosong

        with open('responses.json', 'r') as f:
            content = f.read().strip()
            if not content:
                return []  # Jika file kosong, kembalikan array kosong
            
            return json.loads(content)  # Parse JSON
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Jika error, kembalikan array kosong

# Endpoint untuk menampilkan pertanyaan berdasarkan ID
@app.route('/view/<id>')
def view_response(id):
    responses = get_all_responses()
    for response in responses:
        if response.get('id') == id:
            return render_template('view.html', response=response)
    return "Response not found", 404

@app.route('/history', methods=['GET'])
def history():
    responses = get_all_responses()[::-1]  # Urutkan dari terbaru ke terlama

    # Ambil hanya 5 data terbaru
    latest_responses = responses[:10]

    return jsonify({
        "data": latest_responses,
        "total": len(latest_responses)
    })

# Halaman utama untuk input pertanyaan
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
