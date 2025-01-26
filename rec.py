import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load the fashion dataset
df = pd.read_csv("static/Dress dataset/fashion.csv")


# Fill missing values in the columns
columns = ['gender', 'skintone', 'body shape', 'style']
for col in columns:
    df[col] = df[col].fillna('')

# Combine attributes into a single feature for each row
def combine_features(row):
    # Replace semicolons with spaces in all relevant columns
    gender = row['gender']
    skintone = row['skintone'].replace(";", " ")
    body_shape = row['body shape'].replace(";", " ")
    style = row['style'].replace(";", " ")
    return f"{gender} {skintone} {body_shape} {style}"


df['combined_features'] = df.apply(combine_features, axis=1)

# Vectorize the combined features using CountVectorizer
cv = CountVectorizer()
count_matrix = cv.fit_transform(df['combined_features'])

def get_recommendations(input_gender, input_skintone, input_body_shape, input_style, top_n=5):
    # Combine the user input into a single string
    user_input = f"{input_gender} {input_skintone} {input_body_shape} {input_style}"

    # Vectorize the user input
    user_input_vector = cv.transform([user_input])

    # Calculate similarity between user input and all rows in the dataset
    similarity_scores = cosine_similarity(user_input_vector, count_matrix)

    # Sort rows by similarity scores
    similar_items = list(enumerate(similarity_scores[0]))
    sorted_similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

    # Retrieve the top N matching images
    recommended_images = []
    for item in sorted_similar_items[:top_n]:
        index = item[0]
        image_name = df.loc[index, 'Image']  # Ensure 'Image' column holds the file names
        recommended_images.append(f"Dress dataset/{image_name}")  # Add folder path
    return recommended_images
