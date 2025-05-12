import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from mcp import Tool
import os

logger = logging.getLogger(__name__)

class GetReportSuitesParams(BaseModel):
    limit: Optional[int] = Field(default=50, description="결과 제한")
    page: Optional[int] = Field(default=0, description="페이지 번호")
    expansion: Optional[str] = Field(default=None, description="확장 필드")

class GetReportSuitesTool(Tool):
    name: str = "get_report_suites"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "결과 제한",
                "default": 50
            },
            "page": {
                "type": "integer",
                "description": "페이지 번호",
                "default": 0
            },
            "expansion": {
                "type": "string",
                "description": "확장 필드",
                "default": None
            }
        }
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth

    async def execute(self, params: dict) -> dict:
        """리포트 스위트 목록을 가져옵니다."""
        try:
            logger.info("Getting report suites")
            
            # 파라미터 검증
            validated_params = GetReportSuitesParams(**params)
            
            # API 요청
            async with aiohttp.ClientSession() as session:
                access_token = await self.auth.get_access_token(session)
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "x-api-key": self.auth.client_id,
                    "x-proxy-company-id": self.auth.company_id,
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                url = f"https://analytics.adobe.io/api/{self.auth.company_id}/reportsuites/collections/suites"
                logger.info(f"Request URL: {url}")
                params = {
                    "limit": validated_params.limit,
                    "page": validated_params.page
                }
                if validated_params.expansion:
                    params["expansion"] = validated_params.expansion
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        raise Exception(f"API request failed: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error in get_report_suites: {str(e)}")
            raise 