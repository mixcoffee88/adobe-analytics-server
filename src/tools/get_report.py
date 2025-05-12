import aiohttp
import logging
from auth.adobe_auth import AdobeAuth
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from mcp import Tool
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def parse_date_range(date_range: str) -> str:
    """날짜 범위를 ISO 형식으로 변환"""
    now = datetime.now()

    # 절대 날짜 형식인 경우 (YYYY-MM-DD 또는 YYYY-MM-DD/YYYY-MM-DD)
    if "/" in date_range:
        start_str, end_str = date_range.split("/")
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"잘못된 날짜 형식: {date_range}")
    else:
        try:
            # 단일 날짜인 경우
            start_date = datetime.strptime(date_range, "%Y-%m-%d")
            end_date = start_date
        except ValueError:
            # 상대적 날짜인 경우
            if date_range == "last_3_days":
                start_date = now - timedelta(days=3)
            elif date_range == "last_7_days":
                start_date = now - timedelta(days=7)
            elif date_range == "last_30_days":
                start_date = now - timedelta(days=30)
            elif date_range == "this_week":
                start_date = now - timedelta(days=now.weekday())
            elif date_range == "last_week":
                start_date = now - timedelta(days=now.weekday() + 7)
            elif date_range == "this_month":
                start_date = now.replace(day=1)
            elif date_range == "last_month":
                start_date = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            else:
                raise ValueError(f"지원하지 않는 날짜 범위: {date_range}")
            end_date = now

    # ISO 형식으로 변환 (시간은 00:00:00.000으로 설정)
    start_iso = (
        start_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        + ".000"
    )
    end_iso = (
        end_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + ".000"
    )

    return f"{start_iso}/{end_iso}"


class GetReportParams(BaseModel):
    """리포트 파라미터"""

    date_range: str = Field(
        ..., description="날짜 범위 (예: last_3_days, this_week, last_month)"
    )
    metrics: List[str] = Field(..., description="지표 목록")
    dimension: Optional[str] = Field(
        default="daterangeday", description="차원 (기본값: daterangeday)"
    )
    rsid: Optional[str] = Field(default=None, description="리포트 스위트 ID")
    limit: Optional[int] = Field(default=10, description="결과 제한")
    page: Optional[int] = Field(default=0, description="페이지 번호")


class GetReportTool(Tool):
    name: str = "get_report"
    inputSchema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "date_range": {
                "type": "string",
                "description": "날짜 범위 (예: last_3_days, this_week, last_month)",
            },
            "metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "지표 목록",
            },
            "dimension": {
                "type": "string",
                "description": "차원 (기본값: daterangeday)",
            },
            "rsid": {"type": "string", "description": "리포트 스위트 ID"},
            "limit": {"type": "integer", "description": "결과 제한", "default": 10},
            "page": {"type": "integer", "description": "페이지 번호", "default": 0},
        },
        "required": ["date_range", "metrics"],
    }

    def __init__(self, auth: AdobeAuth):
        super().__init__()
        self.auth = auth

    async def execute(self, params: dict) -> dict:
        """리포트를 실행합니다."""
        try:
            # 파라미터 검증
            validated_params = GetReportParams(**params)

            # rsid가 입력되지 않았을 경우 auth.report_suite_id 사용
            rsid = validated_params.rsid or self.auth.report_suite_id
            if not rsid:
                raise ValueError("리포트 스위트 ID가 설정되지 않았습니다.")

            # 날짜 범위 파싱
            iso_date_range = parse_date_range(validated_params.date_range)

            # API 요청 파라미터 구성
            request_body = {
                "rsid": rsid,
                "globalFilters": [{"type": "dateRange", "dateRange": iso_date_range}],
                "metricContainer": {
                    "metrics": [
                        {"columnId": str(i), "id": f"metrics/{metric}"}
                        for i, metric in enumerate(validated_params.metrics)
                    ]
                },
                "dimension": f"variables/{validated_params.dimension}",
                "settings": {
                    "limit": validated_params.limit,
                    "page": validated_params.page,
                },
            }

            # API 요청
            async with aiohttp.ClientSession() as session:
                access_token = await self.auth.get_access_token(session)

                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "x-api-key": self.auth.client_id,
                    "x-proxy-company-id": self.auth.company_id,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                url = f"https://analytics.adobe.io/api/{self.auth.company_id}/reports"
                logger.info(
                    f"url : { url }, headers : { headers }, params : { request_body }"
                )

                async with session.post(
                    url, headers=headers, json=request_body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            "API 요청 실패 - 상태: %d, 오류: %s",
                            response.status,
                            error_text,
                        )
                        raise Exception(f"API 요청 실패: {error_text}")

                    result = await response.json()
                    return result

        except Exception as e:
            logger.error("리포트 실행 중 오류 발생: %s", str(e))
            raise
