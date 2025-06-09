from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, session, flash
from utils.model_utils import load_models, predict_tabular, get_default_input
from utils.db import create_user, create_verification_token, verify_user, verify_login
from utils.email_utils import send_verification_email
from utils.llm_utils import generate_health_advice  # Removed load_model
from config import SECRET_KEY, DEBUG
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

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

    # Remove LLM model loading (no load_model call needed)
    # logger.info("Loading LLM model...")
    # if not load_model():
    #     logger.warning("LLM model loading failed, will use fallback responses")

except Exception as e:
    logger.error(f"Error during startup: {str(e)}")
    raise

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def calculate_risk_adjustment(family_history, smoking_status, alcohol_consumption):
    """Calculate additional risk percentage based on lifestyle and history factors with scientific evidence"""
    additional_risk = 0.0
    risk_details = []
    
    # Family history risk (10-15% of ovarian cancers are hereditary)
    if family_history == 1:  # First-degree relative
        additional_risk += 0.10  # Reduced from 0.15 to 0.10 for more balanced assessment
        risk_details.append({
            'factor': 'Family History (First-degree relative)',
            'increase': '10%',
            'details': 'Having a first-degree relative with ovarian cancer increases risk.'
        })
    elif family_history == 2:  # Multiple relatives
        additional_risk += 0.15  # Reduced from 0.25 to 0.15 for more balanced assessment
        risk_details.append({
            'factor': 'Family History (Multiple relatives)',
            'increase': '15%',
            'details': 'Multiple family members with ovarian cancer indicates increased risk.'
        })
    
    # Smoking risk (1.2-1.8x higher for mucinous type)
    if smoking_status == 2:  # Current smoker
        additional_risk += 0.05  # Reduced from 0.08 to 0.05
        risk_details.append({
            'factor': 'Current Smoker',
            'increase': '5%',
            'details': 'Smoking may increase risk, particularly for mucinous ovarian cancer.'
        })
    elif smoking_status == 1:  # Former smoker
        additional_risk += 0.02  # Reduced from 0.04 to 0.02
        risk_details.append({
            'factor': 'Former Smoker',
            'increase': '2%',
            'details': 'Former smoking status carries a slightly increased risk.'
        })
    
    # Alcohol consumption (minimal evidence for increased risk)
    if alcohol_consumption >= 3:  # Heavy drinking
        additional_risk += 0.02  # Reduced from 0.03 to 0.02
        risk_details.append({
            'factor': 'Heavy Alcohol Consumption',
            'increase': '2%',
            'details': 'Heavy alcohol consumption may slightly increase risk.'
        })
    
    return additional_risk, risk_details

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/prediction')
def prediction():
    return render_template('index.html')  # Your existing prediction page

@app.route('/predict_lab', methods=['POST'])
def predict_lab():
    try:
        # Add cache control headers
        response = make_response()
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Reload model for fresh prediction
        new_model, new_columns = load_models()
        if new_model is None or new_columns is None:
            raise RuntimeError("Failed to load models for prediction")
            
        # Save globally in case we need them later
        global model, columns
        model, columns = new_model, new_columns

        # Get lifestyle/history factors separately
        family_history = safe_int(request.form.get('family_history', '0'), 0)
        smoking_status = safe_int(request.form.get('smoking_status', '0'), 0)
        alcohol_consumption = safe_int(request.form.get('alcohol_consumption', '0'), 0)

        # Initialize input_data with only the fields we want to update from the form
        input_data = {}
        
        # Map form fields to model features
        form_to_model = {
            'age': 'Age',
            'menopause': 'Menopause',
            'ggt': 'GGT',
            'hgb': 'HGB',
            'afp': 'AFP',
            'ca72_4': 'CA72-4',
            'alp': 'ALP',
            'ca19_9': 'CA19-9',
            'he4': 'HE4',
            'cea': 'CEA',
            'ca125': 'CA125',
            'ca': 'Ca'
        }
        
        # Only update values that were actually provided in the form
        for form_field, model_field in form_to_model.items():
            value = request.form.get(form_field, '')
            if value:  # Only include non-empty values
                if form_field in ['age', 'menopause']:
                    input_data[model_field] = safe_int(value, get_default_input()[model_field])
                else:
                    input_data[model_field] = safe_float(value, get_default_input()[model_field])
        
        logger.info(f"Making prediction with {len(input_data)} features")
            
        # Get model prediction
        result = predict_tabular(model, columns, input_data)
        if result is None:
            return render_template('result.html', 
                                error="Unable to generate prediction. Please try again.",
                                input_data=input_data)
              # Calculate additional risk from lifestyle factors
        additional_risk, risk_details = calculate_risk_adjustment(family_history, smoking_status, alcohol_consumption)
        
        # Scale the additional risk based on the base probability
        # This ensures lifestyle factors have proportional impact
        scaled_additional_risk = additional_risk * result['probability']
        
        # Adjust probability with scaled lifestyle factors (capped at 95%)
        final_probability = min(0.95, result['probability'] + scaled_additional_risk)
        result['probability'] = final_probability
        
        # Determine risk level and styling
        risk_level = "high" if final_probability > 0.7 else "medium" if final_probability > 0.3 else "low"
        risk_color = {
            "high": "text-red-500",
            "medium": "text-yellow-500",
            "low": "text-green-500"
        }[risk_level]

        try:
            # Generate health advice
            advice = generate_health_advice(input_data, result)
            
            # Render template with all results
            return render_template(
                'result.html',
                risk_level=risk_level.upper(),
                risk_color=risk_color,
                probability=f"{final_probability:.1%}",
                advice=advice,
                risk_details=risk_details,
                input_data=input_data,
                now=datetime.now()
            )
            
        except Exception as llm_error:
            logger.error(f"Error generating health advice: {str(llm_error)}")
            # Return basic result if LLM fails
            return render_template(
                'result.html',
                risk_level=risk_level.upper(),
                risk_color=risk_color,
                probability=f"{final_probability:.1%}",
                error="Unable to generate detailed health advice. Please consult with your healthcare provider.",
                input_data=input_data,
                now=datetime.now()
            )
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        logger.error("Form data:", str(dict(request.form)))
        return render_template('result.html', error=f"An error occurred: {str(e)}")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/verify-otp')
def verify_otp():
    return render_template('verify_otp.html')

@app.route('/auth/signup', methods=['POST'])
def auth_signup():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Create user
        user = create_user(email, password, name)
        if not user:
            raise ValueError("Failed to create user")
            
        # Generate and send verification token
        token = create_verification_token(user['id'])
        if not token:
            raise ValueError("Failed to create verification token")
            
        # Send email
        if not send_verification_email(email, name, token):
            raise ValueError("Failed to send verification email")
            
        # Store user_id in session for OTP verification
        session['temp_user_id'] = user['id']
        
        return redirect(url_for('verify_otp'))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return redirect(url_for('signup'))

@app.route('/auth/verify-otp', methods=['POST'])
def auth_verify_otp():
    try:
        # Get OTP digits and combine them
        token = request.form.get('otp', '')  # Try getting full OTP first
        if not token:
            # If no full OTP, try combining digits
            token = ''.join([request.form.get(f'digit{i}', '') for i in range(6)])
        
        user_id = session.get('temp_user_id')
        
        if not user_id:
            logger.error("No user_id found in session")
            flash('Invalid session. Please try signing up again.')
            return redirect(url_for('signup'))
        
        if not token or len(token) != 6:
            logger.error(f"Invalid token format: {token}")
            flash('Please enter a valid 6-digit code.')
            return redirect(url_for('verify_otp'))
            
        if verify_user(user_id, token):
            # Clear session and redirect to login
            session.pop('temp_user_id', None)
            flash('Email verified successfully! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired verification code.')
            return redirect(url_for('verify_otp'))
            
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        flash('An error occurred during verification.')
        return redirect(url_for('verify_otp'))

@app.route('/auth/login', methods=['POST'])
def auth_login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = verify_login(email, password)
        if not user:
            flash('Invalid credentials')
            return redirect(url_for('login'))
            
        if not user['email_verified']:
            flash('Please verify your email first')
            return redirect(url_for('login'))
            
        # Set session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        
        # Redirect to prediction page instead of index
        return redirect(url_for('prediction'))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash('An error occurred during login')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
    