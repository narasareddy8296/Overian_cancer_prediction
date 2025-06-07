import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Email configuration
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Email templates
EMAIL_TEMPLATES = {
    'verification': {
        'subject': 'Verify your email - Ovarian Cancer Risk Assessment',
        'body': '''
            Hello {name},
            
            Your verification code is: {code}
            
            This code will expire in 10 minutes.
            
            Best regards,
            Ovarian Cancer Risk Assessment Team
        '''
    }
}

# Hugging Face configuration
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')  # Your provided token
MODEL_ID = os.getenv('MODEL_ID')  # Updated model

# App configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
