from flask import Flask, request, render_template, url_for
import os
import subprocess

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/personalize', methods=['GET', 'POST'])
def personalize():
    if request.method == 'POST':
        image = request.files.get('image')  # Get the uploaded image
        if image:
            # Save the uploaded image
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            
            # Execute faceshape.py and capture its output
            try:
                result = subprocess.run(
                    ['python', 'faceshape.py', image_path],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout.strip()  # Standard output from faceshape.py
                
                # Extract the face shape (assumes it is the last line of the output)
                face_shape = output.split('\n')[-1]
                
                # Assume processed image is saved as 'output.jpg' by faceshape.py
                processed_image_path = os.path.join('static', 'processed_images', 'output.jpg')
                os.makedirs(os.path.dirname(processed_image_path), exist_ok=True)
                
                if os.path.exists('output.jpg'):
                    os.rename('output.jpg', processed_image_path)

                return render_template(
                    'personalize.html',
                    uploaded=True,
                    face_shape=face_shape,
                    processed_image=os.path.basename(processed_image_path)
                )
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or str(e)
                return render_template('personalize.html', uploaded=False, error=error_output)

    return render_template('personalize.html', uploaded=False)


if __name__ == '__main__':
    app.run(debug=True)
