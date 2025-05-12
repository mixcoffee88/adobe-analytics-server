import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import aiohttp
from typing import Optional

# 로깅 설정
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

class AdobeAuth:
    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.company_id = os.getenv("COMPANY_ID")
        self.report_suite_id = os.getenv("REPORT_SUITE_ID")
        self.token_endpoint = os.getenv("TOKEN_ENDPOINT")
        self.scopes = os.getenv("SCOPES")
        
        self.access_token = None
        self.token_expires_at = None
        
        if not all([self.client_id, self.client_secret, self.company_id, self.report_suite_id, self.token_endpoint, self.scopes]):
            raise ValueError("Missing required environment variables")

    async def get_access_token(self, session: aiohttp.ClientSession) -> str:
        """액세스 토큰을 가져옵니다."""
        try:
            if self.access_token and self.token_expires_at and self.token_expires_at > datetime.now():
                return self.access_token
                
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": self.scopes
            }
            
            async with session.post(self.token_endpoint, headers=headers, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    self.token_expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])
                    return self.access_token
                else:
                    error_text = await response.text()
                    logger.error("토큰 요청 실패: %s", error_text)
                    raise Exception(f"Token request failed: {error_text}")
                    
        except Exception as e:
            logger.error("토큰 획득 실패: %s", str(e))
            raise 