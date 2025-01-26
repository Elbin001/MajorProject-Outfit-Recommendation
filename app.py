from flask import Flask, request, render_template, url_for
import os
import subprocess
from rec import get_recommendations  # Import the recommendation logic
from flask import session
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
            
            # Initialize variables for results and errors
            faceshape_result, faceshape_error = None, None
            main_result, main_error = None, None

            # Execute faceshape.py
            try:
                faceshape_process = subprocess.run(
                    ['python', 'faceshape.py', image_path],
                    capture_output=True, text=True, check=True
                )
                faceshape_result = faceshape_process.stdout.strip().split('\n')[-1]
            except subprocess.CalledProcessError as e:
                faceshape_error = e.stderr or str(e)

            # Execute __main__.py located in the "skintone" folder
            try:
                main_process = subprocess.run(
                    ['python', os.path.join('skintone', '__main__.py'), image_path],
                    capture_output=True, text=True, check=True
                )
                main_result = main_process.stdout.strip().split('\n')[-1]
            except subprocess.CalledProcessError as e:
                main_error = e.stderr or str(e)

            # Assume processed images (if any) are saved by each script
            processed_image_path_faceshape = os.path.join('static', 'processed_images', 'faceshape_output.jpg')
            processed_image_path_main = os.path.join('static', 'processed_images', 'main_output.jpg')
            os.makedirs(os.path.dirname(processed_image_path_faceshape), exist_ok=True)

            if os.path.exists('faceshape_output.jpg'):
                os.rename('faceshape_output.jpg', processed_image_path_faceshape)

            if os.path.exists('main_output.jpg'):
                os.rename('main_output.jpg', processed_image_path_main)

            # Render the template with results and errors
            return render_template(
                'personalize.html',
                uploaded=True,
                faceshape_result=faceshape_result,
                faceshape_error=faceshape_error,
                main_result=main_result,
                main_error=main_error,
                faceshape_image=os.path.basename(processed_image_path_faceshape) if os.path.exists(processed_image_path_faceshape) else None,
                main_image=os.path.basename(processed_image_path_main) if os.path.exists(processed_image_path_main) else None
            )

    return render_template('personalize.html', uploaded=False)
@app.route('/outfit', methods=['POST'])
def outfit():
    # Extract user selections from the form
    face_shape = request.form.get('face_shape', "Not detected")
    skin_tone = request.form.get('skin_tone', "Not detected")
    gender = request.form.get('gender', "Not selected")
    body = request.form.get('body_shape', "Not selected")
    style = request.form.get('style', "Not selected")

    # Get recommendations
    recommendations = get_recommendations(gender, skin_tone, body, style)

    return render_template(
        'outfit.html',
        face_shape=face_shape,
        skin_tone=skin_tone,
        gender=gender,
        body=body,
        style=style,
        recommendations=recommendations
    )
if __name__ == '__main__':
    app.run(debug=True)
