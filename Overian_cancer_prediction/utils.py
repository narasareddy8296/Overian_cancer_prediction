import os
import joblib
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define base directory and model paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

def get_default_features():
    """Return dictionary of default features and their values"""
    return {
        'SUBJECT_ID': 0, 'AFP': 0.0, 'AG': 0.0, 'Age': 0, 'ALB': 0.0,
        'ALP': 0.0, 'ALT': 0.0, 'AST': 0.0, 'BASO#': 0.0, 'BASO%': 0.0,
        'BUN': 0.0, 'Ca': 0.0, 'CA125': 0.0, 'CA19-9': 0.0, 'CA72-4': 0.0,
        'CEA': 0.0, 'CL': 0.0, 'CO2CP': 0.0, 'CREA': 0.0, 'TYPE': 0,
        'DBIL': 0.0, 'EO#': 0.0, 'EO%': 0.0, 'GGT': 0.0, 'GLO': 0.0,
        'GLU.': 0.0, 'HCT': 0.0, 'HE4': 0.0, 'HGB': 0.0, 'IBIL': 0.0,
        'K': 0.0, 'LYM#': 0.0, 'LYM%': 0.0, 'MCH': 0.0, 'MCV': 0.0,
        'Menopause': 0, 'Mg': 0.0, 'MONO#': 0.0, 'MONO%': 0.0, 'MPV': 0.0,
        'Na': 0.0, 'NEU': 0.0, 'PCT': 0.0, 'PDW': 0.0, 'PHOS': 0.0,
        'PLT': 0.0, 'RBC': 0.0, 'RDW': 0.0, 'TBIL': 0.0, 'TP': 0.0, 'UA': 0.0
    }

def load_models(save_columns=False):
    """Load the models and required files"""
    try:
        # Get absolute path to models directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(current_dir, 'models')
        
        # Define paths
        model_path = os.path.join(models_dir, 'xgboost_model.pkl')
        columns_path = os.path.join(models_dir, 'model_columns.pkl')
        
        logger.info(f"Looking for models in: {models_dir}")
        
        # Check directory exists
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            logger.info(f"Created models directory at: {models_dir}")
        
        # Load model file
        try:
            model = joblib.load(model_path)
            logger.info("Model loaded successfully")
        except FileNotFoundError:
            logger.error(f"Model file not found at: {model_path}")
            raise
        
        # Load or initialize columns
        try:
            columns = pd.read_pickle(columns_path)
            logger.info("Columns file loaded successfully")
        except FileNotFoundError:
            logger.warning("Columns file not found - initializing with default features")
            # Initialize with actual feature names
            default_features = get_default_features()
            sample_data = pd.DataFrame([default_features])
            columns = pd.get_dummies(sample_data).columns.tolist()
            
            if save_columns:
                save_columns_file(columns, columns_path)
                logger.info("Saved default columns configuration")
        
        return model, columns
        
    except Exception as e:
        logger.error(f"Error in load_models: {str(e)}")
        return None, None

def save_columns_file(columns, path=None):
    """Save columns to pickle file"""
    try:
        if path is None:
            path = os.path.join(MODELS_DIR, 'model_columns.pkl')
        pd.Series(columns).to_pickle(path)
        logger.info(f"Saved columns file to: {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving columns file: {str(e)}")
        return False

def predict_tabular(model, model_columns, input_data):
    """Make prediction using tabular data"""
    try:
        # Create DataFrame and encode
        df = pd.DataFrame([input_data])
        
        # Get dummies and ensure all required columns are present
        df_encoded = pd.get_dummies(df)
        missing_cols = set(model_columns) - set(df_encoded.columns)
        for c in missing_cols:
            df_encoded[c] = 0
            
        # Ensure columns are in the right order
        df_encoded = df_encoded.reindex(columns=model_columns, fill_value=0)
        
        # Verify data shape
        logger.info(f"Input data shape: {df_encoded.shape}")
        logger.info(f"Expected columns: {len(model_columns)}")
        
        # Make prediction
        prediction = model.predict(df_encoded)[0]
        probability = float(model.predict_proba(df_encoded)[0][1])
        
        logger.info(f"Prediction made: {prediction}, Probability: {probability}")
        
        return {
            'prediction': int(prediction),
            'probability': probability
        }
    except Exception as e:
        logger.error(f"Prediction error in predict_tabular: {str(e)}")
        return None
