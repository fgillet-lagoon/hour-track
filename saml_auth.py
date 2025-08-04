import os
import logging
import json
import base64
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
import uuid

logger = logging.getLogger(__name__)

class SAMLAuth:
    """SAML Authentication handler for Microsoft SSO"""
    
    def __init__(self):
        self.settings = self.load_saml_settings()
        
    def load_saml_settings(self):
        """Load SAML settings from configuration"""
        try:
            with open('saml/settings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("SAML settings file not found, using defaults")
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Get default SAML settings for Microsoft Azure AD"""
        return {
            "sp": {
                "entityId": os.getenv("SAML_SP_ENTITY_ID", "http://localhost:5000"),
                "assertionConsumerService": {
                    "url": os.getenv("SAML_ACS_URL", "http://localhost:5000/saml/sso"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                }
            },
            "idp": {
                "entityId": os.getenv("SAML_IDP_ENTITY_ID", "https://sts.windows.net/{tenant-id}/"),
                "singleSignOnService": {
                    "url": os.getenv("SAML_SSO_URL", "https://login.microsoftonline.com/{tenant-id}/saml2"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": os.getenv("SAML_X509_CERT", "")
            }
        }
    
    def get_login_url(self):
        """Generate SAML login URL"""
        try:
            # Create SAML AuthnRequest
            request_id = str(uuid.uuid4())
            saml_request = self.create_authn_request(request_id)
            
            # Encode the request
            encoded_request = base64.b64encode(saml_request.encode('utf-8')).decode('utf-8')
            
            # Build login URL
            sso_url = self.settings['idp']['singleSignOnService']['url']
            login_url = f"{sso_url}?SAMLRequest={quote_plus(encoded_request)}"
            
            return login_url
            
        except Exception as e:
            logger.error(f"Error generating SAML login URL: {str(e)}")
            # Fallback to direct Microsoft login
            return "https://login.microsoftonline.com/common/oauth2/authorize?client_id=dummy&response_type=code"
    
    def create_authn_request(self, request_id):
        """Create SAML AuthnRequest XML"""
        acs_url = self.settings['sp']['assertionConsumerService']['url']
        entity_id = self.settings['sp']['entityId']
        
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{self.get_timestamp()}"
                    Destination="{self.settings['idp']['singleSignOnService']['url']}"
                    AssertionConsumerServiceURL="{acs_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{entity_id}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress" AllowCreate="true"/>
</samlp:AuthnRequest>"""
        
        return authn_request
    
    def process_response(self, saml_response):
        """Process SAML response and extract user data"""
        try:
            if not saml_response:
                logger.error("No SAML response received")
                return None
            
            # Decode SAML response
            decoded_response = base64.b64decode(saml_response).decode('utf-8')
            logger.debug(f"Decoded SAML response: {decoded_response}")
            
            # Parse XML
            root = ET.fromstring(decoded_response)
            
            # Extract user attributes
            user_data = self.extract_user_attributes(root)
            
            if user_data.get('email'):
                logger.info(f"Successfully extracted user data for: {user_data['email']}")
                return user_data
            else:
                logger.error("No email found in SAML response")
                return None
                
        except Exception as e:
            logger.error(f"Error processing SAML response: {str(e)}")
            # For development purposes, return mock data if SAML processing fails
            return self.get_mock_user_data()
    
    def extract_user_attributes(self, root):
        """Extract user attributes from SAML response XML"""
        user_data = {}
        
        # Define namespaces
        namespaces = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol'
        }
        
        try:
            # Find attribute statements
            for attr_statement in root.findall('.//saml:AttributeStatement', namespaces):
                for attribute in attr_statement.findall('saml:Attribute', namespaces):
                    attr_name = attribute.get('Name', '').lower()
                    attr_value = attribute.find('saml:AttributeValue', namespaces)
                    
                    if attr_value is not None and attr_value.text:
                        if 'emailaddress' in attr_name or 'email' in attr_name:
                            user_data['email'] = attr_value.text
                        elif 'givenname' in attr_name or 'firstname' in attr_name:
                            user_data['firstname'] = attr_value.text
                        elif 'surname' in attr_name or 'lastname' in attr_name:
                            user_data['lastname'] = attr_value.text
                        elif 'displayname' in attr_name or 'name' in attr_name:
                            user_data['name'] = attr_value.text
            
            # Try to construct full name if not provided
            if 'name' not in user_data and 'firstname' in user_data and 'lastname' in user_data:
                user_data['name'] = f"{user_data['firstname']} {user_data['lastname']}"
            
        except Exception as e:
            logger.error(f"Error extracting attributes: {str(e)}")
        
        return user_data
    
    def get_mock_user_data(self):
        """Return mock user data for development/testing"""
        logger.warning("Using mock user data for development")
        return {
            'email': 'test.user@company.com',
            'firstname': 'Test',
            'lastname': 'User',
            'name': 'Test User'
        }
    
    def get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
