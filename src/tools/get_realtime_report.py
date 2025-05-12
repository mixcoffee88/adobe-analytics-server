import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from mcp import Tool
import os
import datetime
import pytz

logger = logging.getLogger(__name__)

# 실시간 리포트에서 사용 가능한 메트릭 목록
REALTIME_METRICS = {
    "occurrences": "metrics/occurrences",  # 페이지뷰
    "visitors": "metrics/visitors",        # 방문자
    "instances": "metrics/instances",      # 이벤트 발생
    "bounces": "metrics/bounces",          # 이탈
    "entries": "metrics/entries",          # 진입
    "exits": "metrics/exits"               # 이탈
}

class GetRealtimeReportParams(BaseModel):
    rsid: str = Field(..., description="리포트 스위트 ID")
    metrics: List[str] = Field(..., description="지표 목록 (occurrences, visitors, instances, bounces, entries, exits)")
    elements: Optional[List[str]] = Field(default=None, description="차원 목록")
    date_granularity: Optional[str] = Field(default="minute", description="날짜 단위 (minute, hour, day)")

class GetRealtimeReportTool(Tool):
    name: str = "get_realtime_report"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "rsid": {
                "type": "string",
                "description": "리포트 스위트 ID"
            },
            "metrics": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(REALTIME_METRICS.keys())
                },
                "description": "지표 목록 (occurrences, visitors, instances, bounces, entries, exits)"
            },
            "elements": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "차원 목록",
                "default": None
            },
            "date_granularity": {
                "type": "string",
                "description": "날짜 단위 (minute, hour, day)",
                "default": "minute"
            }
        },
        "required": ["rsid", "metrics"]
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth
        
    async def execute(self, params: dict) -> dict:
        """실시간 리포트 데이터를 가져옵니다."""
        try:
            # 파라미터 검증
            validated_params = GetRealtimeReportParams(**params)
            
            # 메트릭 ID 변환
            metrics = [REALTIME_METRICS[metric] for metric in validated_params.metrics]
            
            # 현재 시간 기준으로 30분 범위 설정
            now = datetime.datetime.now(pytz.UTC)
            start_time = now - datetime.timedelta(minutes=30)
            date_range = f"{start_time.strftime('%Y-%m-%dT%H:%M:%S')}/{now.strftime('%Y-%m-%dT%H:%M:%S')}"
            
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
                
                url = f"https://analytics.adobe.io/api/{self.auth.company_id}/reports/realtime"
                
                # 요청 본문 구성
                request_body = {
                    "rsid": validated_params.rsid,
                    "globalFilters": [
                        {
                            "type": "dateRange",
                            "dateRange": date_range
                        }
                    ],
                    "metricContainer": {
                        "metrics": [
                            {
                                "columnId": str(i),
                                "id": metric
                            } for i, metric in enumerate(metrics)
                        ]
                    },
                    "dimensions": [
                        {
                            "id": "variables/daterangeminute",
                            "dimensionColumnId": "0"
                        }
                    ] + ([{
                        "id": element,
                        "dimensionColumnId": str(i+1)
                    } for i, element in enumerate(validated_params.elements)] if validated_params.elements else []),
                    "settings": {
                        "realTimeMinuteGranularity": 10,
                        "dateGranularity": validated_params.date_granularity
                    }
                }
                
                async with session.post(url, headers=headers, json=request_body) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error("API 요청 실패: %s", error_text)
                        raise Exception(f"API request failed: {error_text}")
                    
        except Exception as e:
            logger.error("실시간 리포트 조회 실패: %s", str(e))
            raise

def get_realtime_report(limit: int = 20, page: int = 0) -> dict:
    """실시간 리포트를 가져오는 함수"""
    tool = GetRealtimeReportTool()
    return tool.execute(GetRealtimeReportParams(limit=limit, page=page))

if __name__ == "__main__":
    import asyncio
    asyncio.run(get_realtime_report()) 