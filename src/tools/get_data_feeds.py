import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from mcp import Tool

logger = logging.getLogger(__name__)

class GetDataFeedsParams(BaseModel):
    """데이터 피드 파라미터"""
    limit: Optional[int] = Field(default=10, description="결과 제한")
    page: Optional[int] = Field(default=0, description="페이지 번호")

class GetDataFeedsTool(Tool):
    name: str = "get_data_feeds"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "결과 제한",
                "default": 10
            },
            "page": {
                "type": "integer",
                "description": "페이지 번호",
                "default": 0
            }
        }
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth

    async def execute(self, params: dict) -> dict:
        """데이터 피드 목록을 조회합니다."""
        try:
            # 파라미터 검증
            validated_params = GetDataFeedsParams(**params)
            
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
                
                url = f"https://analytics.adobe.io/api/{self.auth.company_id}/datafeeds"
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("API 요청 실패 - 상태: %d, 오류: %s", response.status, error_text)
                        raise Exception(f"API 요청 실패: {error_text}")
                        
                    result = await response.json()
                    return result
                    
        except Exception as e:
            logger.error("데이터 피드 조회 중 오류 발생: %s", str(e))
            raise 