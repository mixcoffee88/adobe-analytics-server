import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from mcp import Tool
import os

logger = logging.getLogger(__name__)

class GetDimensionsParams(BaseModel):
    rsid: str = Field(..., description="리포트 스위트 ID")
    limit: Optional[int] = Field(default=50, description="결과 제한")
    page: Optional[int] = Field(default=0, description="페이지 번호")

class GetDimensionsTool(Tool):
    name: str = "get_dimensions"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "rsid": {
                "type": "string",
                "description": "리포트 스위트 ID"
            },
            "limit": {
                "type": "integer",
                "description": "결과 제한",
                "default": 50
            },
            "page": {
                "type": "integer",
                "description": "페이지 번호",
                "default": 0
            }
        },
        "required": ["rsid"]
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth

    async def execute(self, params: dict) -> dict:
        """차원 목록을 가져옵니다."""
        try:
            logger.info("Getting dimensions for RSID: %s", params.get('rsid'))
            
            # 파라미터 검증
            validated_params = GetDimensionsParams(**params)
            
            # API 요청
            async with aiohttp.ClientSession() as session:
                access_token = await self.auth.get_access_token(session)
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "x-api-key": self.auth.client_id,
                    "x-proxy-company-id": self.auth.company_id,
                    "Content-Type": "application/json"
                }
                
                # URL 파라미터 구성
                url = f"https://analytics.adobe.io/api/{self.auth.company_id}/dimensions"
                request_params = {
                    "rsid": validated_params.rsid
                }
                
                if validated_params.limit:
                    request_params["limit"] = validated_params.limit
                
                if validated_params.page:
                    request_params["page"] = validated_params.page
                
                async with session.get(url, headers=headers, params=request_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("API request failed with status %d: %s", response.status, error_text)
                        raise Exception(f"API request failed: {error_text}")
                        
                    result = await response.json()
                    
                    # 응답 형식에 따라 적절히 처리
                    if isinstance(result, dict):
                        content = result.get('content', [])
                        count = len(content)
                    else:
                        content = result
                        count = len(result)
                    
                    logger.info("Successfully retrieved dimensions (count: %d)", count)
                    return {"content": content}
                    
        except Exception as e:
            logger.error("Error in get_dimensions: %s", str(e), exc_info=True)
            raise 