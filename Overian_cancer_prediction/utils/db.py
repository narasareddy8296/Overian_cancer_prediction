import logging
from datetime import datetime, timedelta
import pytz
from supabase import create_client
import bcrypt
from config import SUPABASE_URL, SUPABASE_KEY

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user(email, password, full_name):
    try:
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert user
        user = supabase.table('users').insert({
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
        }).execute()
        
        if user.data:
            return user.data[0]
        return None
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None

def create_verification_token(user_id):
    try:
        from utils.email_utils import generate_verification_code
        token = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        result = supabase.table('email_verification').insert({
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at.isoformat()
        }).execute()
        
        return token if result.data else None
    except Exception as e:
        print(f"Error creating verification token: {str(e)}")
        return None

def verify_user(user_id, token):
    try:
        logger.info(f"Verifying token {token} for user {user_id}")
        
        # Check token with specific user_id and not used
        result = supabase.table('email_verification').select('*')\
            .eq('user_id', user_id)\
            .eq('token', token)\
            .eq('used', False)\
            .execute()
        
        logger.info(f"Verification query result: {result.data}")
        
        if not result.data:
            logger.error(f"No valid token found for user {user_id}")
            return False
        
        verification = result.data[0]
        
        # Convert expiry time to UTC timezone-aware datetime
        expires_at = datetime.fromisoformat(verification['expires_at'].replace('Z', '+00:00'))
        current_time = datetime.now(pytz.UTC)
        
        if current_time > expires_at:
            logger.error("Token expired")
            return False
            
        # Update user and token
        supabase.table('users')\
            .update({'email_verified': True})\
            .eq('id', user_id)\
            .execute()
            
        supabase.table('email_verification')\
            .update({'used': True})\
            .eq('id', verification['id'])\
            .execute()
        
        logger.info(f"Successfully verified user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying user: {str(e)}")
        return False

def verify_login(email, password):
    try:
        result = supabase.table('users').select('*').eq('email', email).execute()
        if not result.data:
            return None
            
        user = result.data[0]
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return None
            
        # Update last login
        supabase.table('users').update({'last_login': datetime.utcnow().isoformat()}).eq('id', user['id']).execute()
        
        return user
    except Exception as e:
        print(f"Error verifying login: {str(e)}")
        return None
