from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify
import os
from main_pro import *

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def process_uploaded_zip(file, detection_type):
    filename = file.filename
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(zip_path)

    response, output_image_path, Width, Height, Position = analyze_zip(file, detection_type)
    return response, os.path.basename(output_image_path), Width, Height, Position


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return redirect(request.url)

    detection_type = request.form.get('detection_type')
    if detection_type not in ['damage', 'equipment']:
        return "Type de détection invalide. Veuillez choisir 'damage' ou 'equipment'.", 400

    response, output_image_filename, Width, Height, Position = process_uploaded_zip(file, detection_type)
    space_detection = int(Width * Height) if Width and Height else None
    print(f"Processed output filename: {output_image_filename}")

    return render_template(
        'result2.html',
        response=response,
        image_filename=output_image_filename,
        Width=Width,
        Height=Height,
        space_detection=space_detection,
        Position=Position
    )


@app.route('/upload_zip', methods=['POST'])
def upload_zip_json():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': 'Invalid file type'}), 400

    detection_type = request.form.get('detection_type')
    if detection_type not in ['damage', 'equipment']:
        return jsonify({
            'error': 'Missing or invalid detection_type. Must be \"damage\" or \"equipment\".'
        }), 400

    try:
        response_text, output_image_filename, Width, Height, Position = process_uploaded_zip(file, detection_type)
        space_detection = int(Width * Height) if Width and Height else None

        response_json = {
            'type': response_text,
            'width_mm': Width,
            'height_mm': Height,
            'surface_mm2': space_detection,
            'position': Position,
            'annotated_image_url': url_for('output_file', filename=output_image_filename, _external=True)
        }

        return jsonify(response_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
