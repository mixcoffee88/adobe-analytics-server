import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from mcp import Tool
import os

logger = logging.getLogger(__name__)


class GetMetricsParams(BaseModel):
    rsid: str = Field(..., description="리포트 스위트 ID")
    limit: Optional[int] = Field(default=50, description="결과 제한")
    page: Optional[int] = Field(default=0, description="페이지 번호")
    max_results: Optional[int] = Field(default=1000, description="최대 결과 수")


class GetMetricsTool(Tool):
    name: str = "get_metrics"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "rsid": {"type": "string", "description": "리포트 스위트 ID"},
            "limit": {"type": "integer", "description": "결과 제한", "default": 50},
            "page": {"type": "integer", "description": "페이지 번호", "default": 0},
            "max_results": {
                "type": "integer",
                "description": "최대 결과 수",
                "default": 1000,
            },
        },
        "required": ["rsid"],
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth

    async def execute(self, params: dict) -> dict:
        """지표 목록을 가져옵니다."""
        try:
            validated_params = GetMetricsParams(**params)
            logger.info(
                "메트릭 조회 시작 - RSID: %s, 페이지: %d, 제한: %d",
                validated_params.rsid,
                validated_params.page,
                validated_params.limit,
            )

            all_metrics: List[Dict] = []
            current_page = validated_params.page
            total_count = 0

            while True:
                async with aiohttp.ClientSession() as session:
                    access_token = await self.auth.get_access_token(session)

                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "x-api-key": self.auth.client_id,
                        "x-proxy-company-id": self.auth.company_id,
                        "Content-Type": "application/json",
                    }

                    url = (
                        f"https://analytics.adobe.io/api/{self.auth.company_id}/metrics"
                    )
                    request_params = {
                        "rsid": validated_params.rsid,
                        "limit": validated_params.limit,
                        "page": current_page,
                    }

                    logger.error(
                        f"url : { url }, headers : { headers }, params : { request_params }"
                    )

                    async with session.get(
                        url, headers=headers, params=request_params
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(
                                "API 요청 실패 - 상태: %d, 오류: %s",
                                response.status,
                                error_text,
                            )
                            raise Exception(f"API 요청 실패: {error_text}")

                        data = await response.json()
                        result = [
                            {
                                "id": item["id"],
                                "title": item["title"],
                                "category": item["category"],
                            }
                            for item in data
                        ]

                        if isinstance(result, dict):
                            content = result.get("content", [])
                            total_count = result.get("totalElements", len(content))
                        else:
                            content = result
                            total_count = len(result)

                        all_metrics.extend(content)

                        # 최대 결과 수 확인
                        if len(all_metrics) >= validated_params.max_results:
                            logger.info(
                                "최대 결과 수(%d) 도달", validated_params.max_results
                            )
                            break

                        # 더 이상 결과가 없으면 종료
                        if not content or len(content) < validated_params.limit:
                            break

                        current_page += 1

            logger.info("메트릭 조회 완료 - 총 %d개 항목", len(all_metrics))
            return {
                "content": all_metrics[: validated_params.max_results],
                "total_count": total_count,
                "returned_count": len(all_metrics[: validated_params.max_results]),
            }

        except Exception as e:
            logger.error("메트릭 조회 중 오류 발생: %s", str(e), exc_info=True)
            raise
