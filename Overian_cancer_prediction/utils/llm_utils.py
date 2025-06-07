import logging
import requests

logger = logging.getLogger(__name__)

TOGETHER_API_KEY = "tgp_v1_MD6iZEhrnGDjnka_olEfwlDYNaxh67Tl-2yMVFUxqU8"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"  # Updated to new model

def generate_health_advice(input_data, prediction_result):
    """Generate personalized health advice using Together AI LLM API"""
    try:
        risk_level = "high" if prediction_result['probability'] > 0.7 else "medium" if prediction_result['probability'] > 0.3 else "low"
        
        # Try to get advice from LLM first
        try:
            llm_advice = generate_llm_advice(input_data, prediction_result, risk_level)
            
            # If any sections are missing, use personalized defaults
            if any(not v or v == "Information not available" for v in llm_advice.values()):
                logger.warning("Some sections were missing in LLM response. Using personalized defaults.")
                return get_personalized_default_advice(
                    risk_level=risk_level,
                    age=input_data.get('Age', 45),
                    is_postmenopausal=bool(input_data.get('Menopause', 0)),
                    marker_levels={
                        'CA125': input_data.get('CA125', 35.0),
                        'HE4': input_data.get('HE4', 40.0),
                        'CA19_9': input_data.get('CA19-9', 15.0)
                    }
                )
            return llm_advice
            
        except Exception as llm_error:
            logger.error(f"Error getting LLM advice: {str(llm_error)}")
            # Fall back to personalized default advice
            return get_personalized_default_advice(
                risk_level=risk_level,
                age=input_data.get('Age', 45),
                is_postmenopausal=bool(input_data.get('Menopause', 0)),
                marker_levels={
                    'CA125': input_data.get('CA125', 35.0),
                    'HE4': input_data.get('HE4', 40.0),
                    'CA19_9': input_data.get('CA19-9', 15.0)
                }
            )
    except Exception as e:
        logger.error(f"Error generating health advice: {str(e)}")
        return get_personalized_default_advice(
            risk_level="medium",  # Default to medium if we can't determine
            age=45,  # Default age
            is_postmenopausal=False,
            marker_levels={}
        )

def generate_llm_advice(input_data, prediction_result, risk_level):
    """Generate advice using LLM"""
    prompt = f"""You are a medical expert providing health recommendations for a patient with ovarian cancer risk assessment. Please provide gentle but informative advice based on the following patient data:

Risk Assessment Results:
- Risk Level: {risk_level.upper()} (Risk Score: {prediction_result['probability']:.1%})
- Age: {input_data['Age']} years
- Menopausal Status: {'Post-menopausal' if input_data['Menopause'] else 'Pre-menopausal'}

Lab Values:
- CA125: {input_data['CA125']} U/mL (Normal Range: 0-35 U/mL)
- HE4: {input_data['HE4']} pmol/L (Normal Range: 0-140 pmol/L)
- CA19-9: {input_data['CA19-9']} U/mL (Normal Range: 0-37 U/mL)
- CEA: {input_data['CEA']} ng/mL
- AFP: {input_data['AFP']} ng/mL

Please provide compassionate and detailed recommendations in these categories. Format each section with bullet points:

1. Risk Factors:
- List both modifiable and non-modifiable risk factors specific to this patient
- Explain how their age and menopausal status affect risk
- Discuss relevant biomarker implications
- Include lifestyle considerations

2. Dietary Recommendations:
- Foods to include based on risk level
- Specific nutrients important for this patient
- Foods to limit or avoid
- Practical meal suggestions

3. Exercise Guidelines:
- Age and risk-appropriate activities
- Recommended frequency and intensity
- Safety precautions based on risk level
- Benefits specific to their situation

4. Important Signs to Monitor:
- Specific symptoms to watch based on risk level
- When to contact healthcare providers
- Recommended screening frequency
- Changes to track in biomarkers

5. Daily Wellness Tips:
- Three personalized daily habits
- Risk-specific stress management
- Sleep recommendations
- Support resources

Please ensure recommendations are specific to the patient's risk level, age, and biomarker values."""

    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a compassionate medical expert specializing in women's health. Provide evidence-based advice while maintaining a supportive tone."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 1500,
        "frequency_penalty": 0.3,
        "presence_penalty": 0.3
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(TOGETHER_API_URL, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    
    data = response.json()
    if "choices" in data and data["choices"]:
        advice_text = data["choices"][0]["message"]["content"].strip()
        return parse_response(advice_text)
    else:
        raise Exception("Unexpected API response format")

def generate_personalized_dietary_advice(risk_level, age, is_postmenopausal):
    """Generate personalized dietary recommendations based on risk factors"""
    recs = []
    
    # Base recommendations for everyone
    base_recs = [
        "Include a variety of colorful fruits and vegetables daily",
        "Choose whole grains over refined grains",
        "Stay well-hydrated with water (aim for 8 glasses daily)"
    ]
    recs.extend(base_recs)
    
    # Risk-level specific recommendations
    if risk_level == "high":
        recs.extend([
            "Prioritize cruciferous vegetables (broccoli, cauliflower, cabbage) - aim for 2-3 servings daily",
            "Include foods rich in antioxidants: berries, leafy greens, green tea, turmeric",
            "Increase fiber intake through legumes and whole grains (25-30g daily)",
            "Limit red meat to once per week or less",
            "Consider limiting dairy products and choosing plant-based alternatives"
        ])
    elif risk_level == "medium":
        recs.extend([
            "Include cruciferous vegetables 3-4 times per week",
            "Add fatty fish rich in omega-3 twice per week",
            "Choose lean proteins over processed meats",
            "Limit added sugars and processed foods"
        ])
    else:
        recs.extend([
            "Include healthy fats from nuts, seeds, and olive oil",
            "Maintain a balanced diet with protein at each meal",
            "Choose fresh, whole foods when possible"
        ])
    
    # Age and menopausal status considerations
    if age > 50 or is_postmenopausal:
        recs.extend([
            "Ensure adequate calcium intake (1200mg daily)",
            "Include vitamin D rich foods or consider supplements",
            "Focus on foods rich in B12 and iron"
        ])
    
    return [r for r in recs if r]  # Filter out any empty strings

def generate_personalized_exercise_advice(risk_level, age):
    """Generate personalized exercise recommendations based on risk factors"""
    recs = []
    
    # Base recommendations
    if age > 60:
        base_activity = "30 minutes of gentle activity"
        intensity = "low to moderate"
    else:
        base_activity = "150 minutes of activity"
        intensity = "moderate"
    
    recs.append(f"Aim for at least {base_activity} per week at {intensity} intensity")
    
    # Activity types based on risk and age
    if risk_level == "high":
        recs.extend([
            "Start with gentle walking and gradually increase intensity",
            "Include balance exercises to maintain stability",
            "Consider working with a certified fitness trainer",
            "Focus on low-impact activities like swimming or stationary cycling"
        ])
    elif age > 60:
        recs.extend([
            "Try gentle yoga or tai chi for balance and flexibility",
            "Include daily walking, starting with 10-15 minutes",
            "Practice simple strength exercises using body weight",
            "Consider water aerobics for joint-friendly activity"
        ])
    else:
        recs.extend([
            "Mix cardio activities like brisk walking, swimming, or cycling",
            "Include strength training 2-3 times per week",
            "Add flexibility exercises or yoga for better mobility",
            "Try group fitness classes for motivation and support"
        ])
    
    # Safety considerations
    safety_tips = [
        "Start slowly and gradually increase duration and intensity",
        "Listen to your body and rest when needed",
        "Stay hydrated before, during, and after exercise",
        f"Consult your healthcare provider before starting any new {intensity} exercise routine"
    ]
    recs.extend(safety_tips)
    
    return recs

def generate_warning_signs(risk_level, age, is_postmenopausal):
    """Generate personalized warning signs to monitor based on risk factors"""
    signs = []
    
    # Common signs for all risk levels
    common_signs = [
        "Persistent bloating or abdominal discomfort",
        "Changes in appetite or feeling full quickly",
        "Unexplained weight changes",
        "Unusual fatigue"
    ]
    signs.extend(common_signs)
    
    # Risk-level specific monitoring
    if risk_level == "high":
        signs.extend([
            "Schedule monthly self-examinations",
            "Monitor any pelvic or lower back pain",
            "Track changes in urinary habits",
            "Note any irregular bleeding",
            f"Get check-ups every {3 if age > 50 else 6} months"
        ])
    elif risk_level == "medium":
        signs.extend([
            "Perform self-examinations every 1-2 months",
            "Monitor energy levels",
            "Track any persistent digestive changes",
            "Schedule regular check-ups every 6-12 months"
        ])
    else:
        signs.extend([
            "Maintain regular self-awareness",
            "Schedule annual check-ups",
            "Keep a health diary if you notice changes"
        ])
    
    # Age and menopausal status considerations
    if age > 50 or is_postmenopausal:
        signs.extend([
            "Monitor bone health and any unusual joint pain",
            "Track changes in sleep patterns",
            "Note any cardiovascular symptoms"
        ])
    
    return signs

def parse_response(text):
    """Parse the LLM response into sections"""
    try:
        # If text is a dict or list, assume it's pre-formatted sections
        if isinstance(text, (dict, list)):
            if isinstance(text, list):
                # Handle list format by converting to sections
                sections = {
                    'risk_factors': text[0] if len(text) > 0 else "Information not available",
                    'diet': text[1] if len(text) > 1 else "Information not available",
                    'exercise': text[2] if len(text) > 2 else "Information not available",
                    'warning_signs': text[3] if len(text) > 3 else "Information not available",
                    'wellness_tips': text[4] if len(text) > 4 else []
                }
            else:
                sections = text
        else:
            # Parse text response into sections
            sections = {
                'risk_factors': extract_section(text, "Risk Factors:", "Dietary Recommendations:"),
                'diet': extract_section(text, "Dietary Recommendations:", "Exercise Guidelines:"),
                'exercise': extract_section(text, "Exercise Guidelines:", "Important Signs"),
                'warning_signs': extract_section(text, "Important Signs", "Daily Wellness"),
                'wellness_tips': extract_wellness_tips(extract_section(text, "Daily Wellness", None))
            }
        
        # Clean up and format sections
        sections = {k: format_section(v) for k, v in sections.items()}
        return sections
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        return get_default_advice()

def format_section(text):
    """Format a section's content into clean HTML with bullet points"""
    if not text or text == "Information not available":
        return "Information not available"
    
    # Handle list input
    if isinstance(text, list):
        formatted_lines = []
        for line in text:
            line = str(line).strip()
            if line:
                # Remove markdown formatting, numbers, and bullets
                line = line.lstrip('0123456789.- *')  # Remove numbers, bullets and markdown
                line = line.replace('***', '').replace('**', '').replace('*', '')  # Remove markdown
                formatted_lines.append(f"<li>{line.strip()}</li>")
        if formatted_lines:
            return f"<ul class='list-disc pl-5 space-y-2'>{''.join(formatted_lines)}</ul>"
        return "Information not available"
    
    # Handle string input
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        # Remove markdown formatting, numbers, and bullets
        line = line.lstrip('0123456789.- *')  # Remove numbers and bullets
        line = line.replace('***', '').replace('**', '').replace('*', '')  # Remove markdown
        if line.startswith('•') or line.startswith('-'):
            line = f"<li>{line.lstrip('•- ')}</li>"
        elif line and not line.startswith('<'):
            formatted_lines.append(f"<p>{line}</p>")
        else:
            formatted_lines.append(line)
    
    if any(line.startswith('<li>') for line in formatted_lines):
        return f"<ul class='list-disc pl-5 space-y-2'>{''.join(formatted_lines)}</ul>"
    return ''.join(formatted_lines)

def get_personalized_default_advice(risk_level, age, is_postmenopausal, marker_levels):
    """Generate personalized default advice based on risk factors"""
    # Get personalized recommendations for each section
    diet_recs = generate_personalized_dietary_advice(risk_level, age, is_postmenopausal)
    exercise_recs = generate_personalized_exercise_advice(risk_level, age)
    warning_signs = generate_warning_signs(risk_level, age, is_postmenopausal)
    
    # Generate risk factors
    risk_factors = get_risk_factor_list(risk_level, age, is_postmenopausal)
    
    # Generate wellness tips based on risk level and age
    if risk_level == "high":
        wellness_tips = [
            f"Schedule regular check-ups every {3 if age > 50 else 6} months and maintain a symptom diary",
            "Practice daily stress reduction through meditation, counseling, or relaxation techniques",
            "Build a strong support network and consider joining a support group"
        ]
    elif risk_level == "medium":
        wellness_tips = [
            "Practice regular relaxation techniques and stress management",
            "Maintain 7-8 hours of quality sleep each night",
            "Stay connected with your healthcare team and support network"
        ]
    else:
        wellness_tips = [
            "Maintain a consistent sleep and exercise routine",
            "Practice mindfulness or meditation for stress management",
            "Stay socially active and maintain regular health check-ups"
        ]

    # Format the advice into HTML
    return {
        'risk_factors': f"""<ul class='list-disc pl-5 space-y-2'>
            {''.join(f"<li>{item}</li>" for item in risk_factors)}
        </ul>""",
        'diet': f"""<ul class='list-disc pl-5 space-y-2'>
            {''.join(f"<li>{item}</li>" for item in diet_recs)}
        </ul>""",
        'exercise': f"""<ul class='list-disc pl-5 space-y-2'>
            {''.join(f"<li>{item}</li>" for item in exercise_recs)}
        </ul>""",
        'wellness_tips': wellness_tips,
        'warning_signs': f"""<ul class='list-disc pl-5 space-y-2'>
            {''.join(f"<li>{item}</li>" for item in warning_signs)}
        </ul>"""
    }

def get_default_advice():
    """Provide basic default advice when personalization fails"""
    return get_personalized_default_advice("medium", 45, False, {})

def get_risk_factor_list(risk_level, age, is_postmenopausal):
    """Generate personalized risk factor list based on patient characteristics"""
    factors = []
    
    # Age-related factors
    if age > 60:
        factors.append("Age is a significant risk factor (risk increases with age)")
        factors.append("Post-60 age group requires more frequent monitoring")
    elif age > 50:
        factors.append("Age is approaching higher risk category (increased vigilance recommended)")
        factors.append("Consider more frequent screenings")
    
    # Menopausal status
    if is_postmenopausal:
        factors.append("Post-menopausal status may increase risk")
        factors.append("Hormonal changes can impact risk factors")
    
    # Risk-level specific factors
    if risk_level == "high":
        factors.extend([
            "Consider genetic counseling and BRCA1/BRCA2 testing",
            "Family history may significantly influence risk level",
            "Regular screening and monitoring is essential",
            "Lifestyle modifications may help manage risk"
        ])
    elif risk_level == "medium":
        factors.extend([
            "Regular monitoring of risk factors recommended",
            "Consider lifestyle modifications for risk reduction",
            "Discuss personalized screening schedule with healthcare provider",
            "Track any changes in symptoms or health status"
        ])
    else:
        factors.extend([
            "Maintain awareness of family health history",
            "Continue regular check-ups and screenings",
            "Monitor any changes in health status",
            "Practice preventive health measures"
        ])
    
    return factors

def extract_section(text, start_marker, end_marker):
    """Extract and clean a section from the response"""
    try:
        # Find the section start
        start_idx = text.lower().find(start_marker.lower())
        if start_idx == -1:
            return "Information not available"
            
        # Move to the content start
        content_start = text.find('\n', start_idx)
        if content_start == -1:
            content_start = start_idx + len(start_marker)
        else:
            content_start += 1
            
        # Find the section end
        if end_marker:
            end_idx = text.lower().find(end_marker.lower(), content_start)
            if end_idx == -1:
                end_idx = len(text)
        else:
            end_idx = len(text)
            
        # Extract and clean the content
        content = text[content_start:end_idx].strip()
        if not content:
            return "Information not available"
            
        return content
    except Exception as e:
        logger.error(f"Error extracting section {start_marker}: {str(e)}")
        return "Information not available"

def extract_wellness_tips(wellness_text):
    """Extract wellness tips into a list of concise, actionable items"""
    try:
        if not wellness_text or wellness_text == "Information not available":
            return get_default_advice()['wellness_tips']
            
        # Handle case where wellness_text is already a list
        if isinstance(wellness_text, list):
            tips = []
            for tip in wellness_text:
                if tip:
                    # Clean up markdown and formatting
                    tip = str(tip).strip('•- *')  # Remove bullets and markdown
                    tip = tip.replace('***', '').replace('**', '')  # Remove markdown
                    tip = tip.lstrip('0123456789.- ')  # Remove numbers
                    if tip.strip():
                        tips.append(tip.strip())
        else:
            # Split text into lines and clean up
            lines = wellness_text.split('\n')
            tips = []
            for line in lines:
                line = line.strip('•- *')  # Remove bullets and markdown
                line = line.replace('***', '').replace('**', '')  # Remove markdown
                line = line.lstrip('0123456789.- ')  # Remove numbers
                if line.strip() and len(line.strip()) > 10:  # Filter out empty/short lines
                    tips.append(line.strip())
        
        if len(tips) >= 3:
            return tips[:3]  # Return first 3 substantial tips
        else:
            # Pad with defaults if needed
            defaults = [
                "Maintain regular health check-ups",
                "Practice stress management through meditation or deep breathing",
                "Ensure adequate sleep and rest"
            ]
            return (tips + defaults)[:3]
    except Exception as e:
        logger.error(f"Error extracting wellness tips: {str(e)}")
        return get_default_advice()['wellness_tips']
