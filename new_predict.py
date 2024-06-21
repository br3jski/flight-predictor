import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, recall_score, f1_score, classification_report
from flask import Flask, request, jsonify
import time
import threading
import numpy as np
import logging
import json
from scipy.sparse import hstack

# --- Global Variables ---
df_combined = None

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Model Initialization ---
model = SGDClassifier()
chunksize = 50000
model_trained = False

# --- Define Preprocessing Steps ---
numeric_features = []  # Nie mamy cech numerycznych w tym przypadku
categorical_features = ['dep_icao']
callsign_feature = 'callsign'

# Initially create preprocessor without the TFIDF vectorizer for callsign
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

callsign_vectorizer = TfidfVectorizer()

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('vectorizer', 'passthrough'),  # Placeholder for callsign vectorizer
    ('classifier', model)
])

global_vocabulary = None

# --- Function to Load & Preprocess Data ---
def load_and_preprocess(filename='output.csv'):
    global global_vocabulary, df_combined
    logger.info("Loading and preprocessing data...")
    data = []
    for chunk in pd.read_csv(filename, chunksize=chunksize):
        try:
            # Ensure 'callsign' is treated as a string
            chunk['callsign'] = chunk['callsign'].astype(str)
            data.append(chunk)
        except Exception as e:
            logger.error(f"Error processing chunk: {e}", exc_info=True)

    logger.info("Data loaded and preprocessed.")
    df_combined = pd.concat(data).reset_index(drop=True)
    X = df_combined.drop(columns=['arr_icao'])
    y = df_combined['arr_icao']

    # Fit the TfidfVectorizer once on the full dataset
    if global_vocabulary is None:
        callsign_vectorizer.fit(X['callsign'])
        global_vocabulary = callsign_vectorizer.vocabulary_
        # Update the pipeline with the fitted vectorizer
        pipeline.set_params(vectorizer=callsign_vectorizer)

    return X, y

# --- Function to Update the Model ---
def update_model(X, y):
    global model_trained
    try:
        logger.info("Updating the model...")
        # Fit the preprocessor if it's not fitted
        X_preprocessed = preprocessor.fit_transform(X)
        # Transform the callsign column
        X_callsign = callsign_vectorizer.transform(X['callsign'])

        # Combine the preprocessed features with the transformed callsign features
        X_combined = hstack([X_preprocessed, X_callsign])

        if not model_trained:
            pipeline.named_steps['classifier'].fit(X_combined, y)
            model_trained = True
        else:
            pipeline.named_steps['classifier'].partial_fit(X_combined, y, classes=np.unique(y))

        y_pred = pipeline.named_steps['classifier'].predict(X_combined)
        accuracy = accuracy_score(y, y_pred)
        recall = recall_score(y, y_pred, average='macro', zero_division=1)
        f1 = f1_score(y, y_pred, average='macro', zero_division=1)

        logger.info(f"Model accuracy: {accuracy:.2f}")
        logger.info(f"Model recall: {recall:.2f}")
        logger.info(f"Model F1 score: {f1:.2f}")

        # Classification report as a dictionary
        report = classification_report(y, y_pred, output_dict=True, zero_division=1)
        report_df = pd.DataFrame(report).transpose()
        logger.info(f"Classification report:\n{report_df}")

    except Exception as e:
        logger.error(f"Error updating model: {e}", exc_info=True)

# --- API Endpoint ---
@app.route('/predict', methods=['GET'])
def predict():
    global df_combined
    data = request.get_json()
    if not data or 'callsign' not in data:
        return jsonify({"error": "Please provide the callsign."}), 400

    try:
        callsign = data['callsign']
        dep_icao = data.get('dep_icao')  # Allow dep_icao to be optional

        # Get the dep_icao value from the dataset based on the callsign
        df_filtered = df_combined.loc[df_combined['callsign'] == callsign, 'dep_icao']
        if df_filtered.empty:
            return jsonify({"error": "Insufficient data"}), 404

        df_dep_icao = df_filtered.values[0]

        # Create DataFrame based on provided features
        X = pd.DataFrame({'callsign': [callsign], 'dep_icao': [dep_icao or df_dep_icao]})

        # Transform the callsign column
        X_callsign = callsign_vectorizer.transform(X['callsign'])
        X_preprocessed = preprocessor.transform(X)

        # Combine the preprocessed features with the transformed callsign features
        X_combined = hstack([X_preprocessed, X_callsign])

        prediction = pipeline.named_steps['classifier'].predict(X_combined)[0]

        # Create a template string with placeholders
        response_template = '{{ "callsign": "{}", "dep_icao": "{}", "arr_icao": "{}" }}'

        # Format the response string with the desired values
        response_str = response_template.format(callsign, df_dep_icao, prediction)
        
        # Using logger log answer
        logger.info(f"Prediction: {response_str}")

        return response_str

    except Exception as e:
        logger.error(f"Error in /predict endpoint: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during prediction."}), 500
    
# --- API Endpoint for HTTP request without JSON ---
@app.route('/predict/<string:callsign>', methods=['GET'])
def predict_by_callsign(callsign):
    global df_combined
    try:
        df_filtered = df_combined.loc[df_combined['callsign'] == callsign, 'dep_icao']
        if df_filtered.empty:
            return jsonify({"error": "Insufficient data"}), 404

        dep_icao = df_filtered.values[0]

        X = pd.DataFrame({'callsign': [callsign], 'dep_icao': [dep_icao]})
        X_callsign = callsign_vectorizer.transform(X['callsign'])
        X_preprocessed = preprocessor.transform(X)
        X_combined = hstack([X_preprocessed, X_callsign])

        prediction = pipeline.named_steps['classifier'].predict(X_combined)[0]

        response_dict = {"callsign": callsign, "dep_icao": dep_icao, "arr_icao": prediction}
        logger.info(f"Prediction: {response_dict}")

        return jsonify(response_dict)

    except Exception as e:
        logger.error(f"Error in /predict/<string:callsign> endpoint: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during prediction."}), 500
    


# --- API Endpoint for Flights from a Specific Airport ---
@app.route('/flights_from_airport', methods=['GET'])
def flights_from_airport():
    global df_combined
    data = request.get_json()
    if not data or 'dep_icao' not in data:
        return jsonify({"error": "Please provide the dep_icao."}), 400

    try:
        dep_icao = data['dep_icao']

        # Filter the dataset based on the dep_icao
        df_filtered = df_combined.loc[df_combined['dep_icao'] == dep_icao, ['callsign', 'arr_icao']]
        if df_filtered.empty:
            return jsonify({"error": "No flights found for the provided dep_icao"}), 404

        # Remove duplicates based on 'callsign' and 'arr_icao'
        df_filtered = df_filtered.drop_duplicates(subset=['callsign', 'arr_icao'])

        # Convert the filtered DataFrame to a list of dictionaries
        flights = df_filtered.to_dict(orient='records')

        return jsonify(flights)

    except Exception as e:
        logger.error(f"Error in /flights_from_airport endpoint: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while fetching flights."}), 500

# --- Main Loop to Continuously Update the Model ---
def continuous_update():
    while True:
        try:
            logger.info("Starting data load and preprocessing...")
            X, y = load_and_preprocess()
            logger.info("Data load and preprocessing completed.")
            if not X.empty:
                logger.info("Starting model update...")
                update_model(X, y)
                logger.info("Model update completed.")
            time.sleep(900)  # Update model every 15 minutes
        except Exception as e:
            logger.error(f"Error in continuous_update: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("Starting continuous update thread...")
    threading.Thread(target=continuous_update).start()
    logger.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
