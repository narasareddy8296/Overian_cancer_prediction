import os
import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

REQUIRED_FEATURES = [
    'Age', 'Menopause', 'GGT', 'HGB', 'AFP', 'CA72-4',
    'ALP', 'CA19-9', 'HE4', 'CEA', 'CA125', 'Ca'
]

def get_default_input():
    """Return only required features with default values"""
    all_defaults = {
        'Age': 45, 'Menopause': 0, 'GGT': 25.0, 'HGB': 14.0,
        'AFP': 2.5, 'CA72-4': 2.0, 'ALP': 70.0, 'CA19-9': 15.0,
        'HE4': 40.0, 'CEA': 2.5, 'CA125': 35.0, 'Ca': 9.5
    }
    return all_defaults

def load_models():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        
        # Check if the model file exists
        if not os.path.exists(models_dir):
            raise FileNotFoundError(f"Models directory not found at {models_dir}")
            
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
        if not model_files:
            raise FileNotFoundError(f"No .pkl model files found in {models_dir}")
            
        model_path = os.path.join(models_dir, model_files[0])  # Take the first .pkl file found
        logger.info(f"Loading model from {model_path}")
        
        model = joblib.load(model_path)
        columns = REQUIRED_FEATURES  # Use only required features
        logger.info("Model loaded successfully")
        return model, columns
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None, None

def predict_tabular(model, columns, input_data):
    try:
        # Validate inputs
        if model is None:
            raise ValueError("Model is not loaded")
        if not columns:
            raise ValueError("No feature columns provided")
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")

        # Start with default values for required features only
        prediction_data = get_default_input()
        logger.info(f"Starting prediction with {len(input_data)} provided features")
        
        # Filter input_data to only include required features
        filtered_input = {k: v for k, v in input_data.items() if k in REQUIRED_FEATURES}
        prediction_data.update(filtered_input)
        
        # Create DataFrame with only required features
        df = pd.DataFrame([prediction_data])
        df = df[columns]  # Ensure correct column order
        
        # Log feature shape
        logger.info(f"Feature shape: {df.shape}, Expected features: {len(columns)}")
        
        # Make prediction
        prediction = model.predict(df)[0]
        probability = float(model.predict_proba(df)[0][1])
        
        logger.info("Prediction successful")
        return {
            'prediction': int(prediction),
            'probability': probability
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        logger.error(f"Input data keys: {list(input_data.keys())}")
        logger.error(f"Expected columns: {columns}")
        return None
