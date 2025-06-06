from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_image(input_path, output_path):
    # Remove background
    with open(input_path, "rb") as input_file:
        with open(output_path, "wb") as output_file:
            input_data = input_file.read()
            output_data = remove(input_data)
            output_file.write(output_data)
    
    # Convert to passport size (typically 2x2 inches at 300 DPI)
    img = Image.open(output_path)
    img = img.resize((600, 600))  # 2x2 inches at 300 DPI
    img.save(output_path)

    # Add white background
    img = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4:  # Check if image has alpha channel
        alpha = img[:,:,3]
        _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
        color = img[:,:,:3]
        new_img = cv2.bitwise_not(cv2.bitwise_not(color, mask=mask))
        new_img = cv2.cvtColor(new_img, cv2.COLOR_BGR2BGRA)
        new_img[:,:,3] = mask
        cv2.imwrite(output_path, new_img)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['RESULT_FOLDER'], filename)
            file.save(input_path)
            
            process_image(input_path, output_path)
            
            return render_template('result.html', 
                                 original=url_for('static', filename='uploads/' + filename),
                                 result=url_for('static', filename='results/' + filename))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
