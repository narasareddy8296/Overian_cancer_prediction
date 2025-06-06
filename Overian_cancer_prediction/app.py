from flask import Flask, render_template, request, jsonify, make_response
from utils import load_models, predict_tabular
import logging
import os
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load models at startup
try:
    # Verify static and template directories exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Load models
    logger.info("Loading models...")
    model, columns = load_models()
    if model is None or columns is None:
        raise RuntimeError("Failed to load models")
    logger.info("Models loaded successfully")
    
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")
    raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict_lab', methods=['POST'])
def predict_lab():
    try:
        # Add cache control headers
        response = make_response()
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Get form data
        input_data = {
            'SUBJECT_ID': int(request.form['patient_id']),
            'AFP': float(request.form['afp']),
            'AG': 20.0,
            'Age': int(request.form['age']),
            'ALB': float(request.form['alb']),
            'ALP': 70.0,
            'ALT': float(request.form['alt']),
            'AST': float(request.form['ast']),
            'BASO#': float(request.form['baso_count']),
            'BASO%': float(request.form['baso_percent']),
            'TYPE': 0,
            'Menopause': int(request.form['menopause']),
            'PLT': int(request.form['plt'])
        }
        
        # Reload model for fresh prediction
        model, columns = load_models()
        if model is None or columns is None:
            raise RuntimeError("Failed to load models for prediction")
            
        # Use predict_tabular from utils
        result = predict_tabular(model, columns, input_data)
        if result is None:
            raise RuntimeError("Prediction failed")
            
        prediction = result['prediction']
        probability = result['probability']
        
        # Calculate risk level
        if probability < 0.3:
            risk_level = "Low Risk"
            risk_class = "bg-green-50 border-green-200 text-green-800"
        elif probability < 0.7:
            risk_level = "Medium Risk"
            risk_class = "bg-yellow-50 border-yellow-200 text-yellow-800"
        else:
            risk_level = "High Risk"
            risk_class = "bg-red-50 border-red-200 text-red-800"

        # Return Tailwind-styled HTML
        result_html = f"""
        <div class="rounded-lg border p-6 text-center {risk_class}">
            <h3 class="text-2xl font-bold mb-4">Cancer Risk Assessment Results</h3>
            <div class="space-y-3">
                <p class="text-xl font-semibold">Risk Level: {risk_level}</p>
                <p class="text-lg">Probability: {probability:.1%}</p>
            </div>
        </div>
        """
        return result_html
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return f'<div class="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4">Error: {str(e)}</div>', 400

if __name__ == '__main__':
    app.run(debug=True)
