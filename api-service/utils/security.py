# api-service/utils/security.py
import re
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class SecurityUtils:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, bool]:
        """Validate password strength"""
        validations = {
            "length": len(password) >= 8,
            "uppercase": bool(re.search(r'[A-Z]', password)),
            "lowercase": bool(re.search(r'[a-z]', password)),
            "digit": bool(re.search(r'\d', password)),
            "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        }
        
        return validations
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not input_str:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = input_str.replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
        sanitized = sanitized.replace('/', '&#x2F;')
        
        return sanitized
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # Check each octet
        octets = ip.split('.')
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                return False
        
        return True
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data for logging"""
        masked_data = data.copy()
        
        sensitive_fields = [
            'password', 'token', 'api_key', 'secret', 
            'credit_card', 'ssn', 'account_number'
        ]
        
        for key in masked_data:
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                if isinstance(masked_data[key], str):
                    masked_data[key] = '*******'
                elif masked_data[key] is not None:
                    masked_data[key] = '*******'
        
        return masked_data
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, stored_token: str) -> bool:
        """Validate CSRF token"""
        import hmac
        return hmac.compare_digest(token, stored_token)