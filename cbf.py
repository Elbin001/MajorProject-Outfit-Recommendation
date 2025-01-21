# Modified Notebook for Fashion Recommendation System

# Install and Import Libraries
!pip install tensorflow keras pandas numpy scikit-learn matplotlib

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder
from tensorflow.keras.applications import VGG16
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.vgg16 import preprocess_input
import matplotlib.pyplot as plt

# Load Metadata and Images
metadata_file = 'fashion_metadata.csv'  # Update this with the path to your metadata CSV
image_folder = 'fashion_images/'         # Folder containing your image dataset

# Load Metadata
metadata = pd.read_csv(metadata_file)
print("Metadata:")
print(metadata.head())

# Extract Features Using Pretrained VGG16
model = VGG16(weights='imagenet', include_top=False, pooling='avg')  # Average pooling for compact features

# Function to Extract Features from Images
def extract_features(image_path):
    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    features = model.predict(img_array)
    return features.flatten()

# Iterate Over Images and Extract Features
image_features = {}
for _, row in metadata.iterrows():
    image_path = f"{image_folder}{row['filename']}"
    features = extract_features(image_path)
    image_features[row['filename']] = features

print("Feature extraction complete.")

# Combine Metadata and Image Features
encoder = OneHotEncoder()
encoded_metadata = encoder.fit_transform(metadata[['gender', 'style', 'skin_tone', 'body_shape']]).toarray()

combined_features = {}
for i, row in metadata.iterrows():
    img_features = image_features[row['filename']]
    meta_features = encoded_metadata[i]
    combined_features[row['filename']] = np.concatenate((img_features, meta_features))

# Prepare Data for KNN
X = np.array(list(combined_features.values()))
filenames = list(combined_features.keys())

# Train KNN Model
knn = NearestNeighbors(n_neighbors=5, metric='cosine')
knn.fit(X)

# Function to Recommend Outfits
def recommend_outfits(input_image_path, user_preferences):
    # Extract features for the input image
    input_img_features = extract_features(input_image_path)

    # Encode user preferences
    user_prefs_encoded = encoder.transform([user_preferences]).toarray()[0]

    # Combine image and user preference features
    query_features = np.concatenate((input_img_features, user_prefs_encoded))

    # Find nearest neighbors
    distances, indices = knn.kneighbors([query_features])
    recommendations = [filenames[i] for i in indices[0]]

    return recommendations

# Example Usage
user_input = {
    'gender': 'female',
    'style': 'casual',
    'skin_tone': 'medium',
    'body_shape': 'pear'
}

input_image = 'path_to_user_uploaded_image.jpg'  # Replace with actual user-uploaded image path
recommendations = recommend_outfits(input_image, list(user_input.values()))
print("Recommended Outfits:", recommendations)

# Visualize Recommendations
for rec in recommendations:
    img_path = f"{image_folder}{rec}"
    img = load_img(img_path, target_size=(224, 224))
    plt.figure()
    plt.imshow(img)
    plt.axis('off')
    plt.title(rec)
    plt.show()
