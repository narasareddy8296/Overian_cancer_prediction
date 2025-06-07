import os
import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_default_input():
    """Return all required features with default values"""
    return {
        'SUBJECT_ID': 999,
        'AFP': 2.5, 'AG': 20.0, 'Age': 45, 'ALB': 4.0,
        'ALP': 70.0, 'ALT': 20.0, 'AST': 20.0,
        'BASO#': 0.1, 'BASO%': 1.0, 'BUN': 15.0,
        'Ca': 9.5, 'CA125': 35.0, 'CA19-9': 15.0,
        'CA72-4': 2.0, 'CEA': 2.5, 'CL': 100.0,
        'CO2CP': 24.0, 'CREA': 0.9, 'TYPE': 0,
        'DBIL': 0.2, 'EO#': 0.2, 'EO%': 2.0,
        'GGT': 25.0, 'GLO': 3.0, 'GLU.': 90.0,
        'HCT': 40.0, 'HE4': 40.0, 'HGB': 14.0,
        'IBIL': 0.8, 'K': 4.0, 'LYM#': 2.0,
        'LYM%': 30.0, 'MCH': 30.0, 'MCV': 90.0,
        'Menopause': 0, 'Mg': 2.0, 'MONO#': 0.5,
        'MONO%': 7.0, 'MPV': 10.0, 'Na': 140.0,
        'NEU': 60.0, 'PCT': 0.2, 'PDW': 12.0,
        'PHOS': 3.5, 'PLT': 250.0, 'RBC': 4.5,
        'RDW': 13.0, 'TBIL': 1.0, 'TP': 7.0,
        'UA': 5.0
    }

def load_models():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        model_path = os.path.join(models_dir, 'xgboost_model.pkl')
        
        model = joblib.load(model_path)
        columns = list(get_default_input().keys())  # Use all features in correct order
        
        logger.info("Model loaded successfully")
        return model, columns
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None, None

def predict_tabular(model, columns, input_data):
    try:
        # Start with default values
        prediction_data = get_default_input()
        
        # Update with provided values
        prediction_data.update(input_data)
        
        # Create DataFrame with all required features
        df = pd.DataFrame([prediction_data])
        
        # Ensure columns are in correct order
        df = df[columns]
        
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
        return None
