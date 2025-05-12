import asyncio
import logging
from src.auth.adobe_auth import AdobeAuth
import aiohttp
import json
from datetime import datetime, timedelta

# 강제 초기화
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_report_api():
    """Report API 테스트"""
    auth = AdobeAuth()
    print("auth : ", auth)
    logger.info("Adobe Analytics Report API 테스트를 시작합니다.")
    logger.info("시작합니다.")
    logger.info(f"Client ID: {auth.client_id}")
    async with aiohttp.ClientSession() as session:
        access_token = await auth.get_access_token(session)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-api-key": auth.client_id,
            "x-proxy-company-id": auth.company_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # 테스트 케이스 1: 일별 방문자 수
        logger.info("테스트 케이스 1: 일별 방문자 수")
        request_body = {
            "rsid": auth.report_suite_id,
            "globalFilters": [
                {
                    "type": "dateRange",
                    "dateRange": "2024-04-01T00:00:00/2024-04-19T23:59:59",
                }
            ],
            "metricContainer": {
                "metrics": [{"columnId": "0", "id": "metrics/visitors"}]
            },
            "dimension": "variables/daterangeday",
            "settings": {"limit": 20},
        }

        async with session.post(
            f"https://analytics.adobe.io/api/{auth.company_id}/reports",
            headers=headers,
            json=request_body,
        ) as response:
            logger.info(f"Response status: {response.status}")
            if response.status == 200:
                result = await response.json()
                logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                error_text = await response.text()
                logger.error(f"API 요청 실패: {error_text}")

        # 테스트 케이스 2: 페이지뷰
        logger.info("테스트 케이스 2: 페이지뷰")
        request_body = {
            "rsid": auth.report_suite_id,
            "globalFilters": [
                {
                    "type": "dateRange",
                    "dateRange": "2024-04-01T00:00:00/2024-04-19T23:59:59",
                }
            ],
            "metricContainer": {
                "metrics": [{"columnId": "0", "id": "metrics/pageviews"}]
            },
            "dimension": "variables/daterangeday",
            "settings": {"limit": 20},
        }

        async with session.post(
            f"https://analytics.adobe.io/api/{auth.company_id}/reports",
            headers=headers,
            json=request_body,
        ) as response:
            logger.info(f"Response status: {response.status}")
            if response.status == 200:
                result = await response.json()
                logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                error_text = await response.text()
                logger.error(f"API 요청 실패: {error_text}")

        # 테스트 케이스 3: 여러 메트릭
        logger.info("테스트 케이스 3: 여러 메트릭")
        request_body = {
            "rsid": auth.report_suite_id,
            "globalFilters": [
                {
                    "type": "dateRange",
                    "dateRange": "2024-04-01T00:00:00/2024-04-19T23:59:59",
                }
            ],
            "metricContainer": {
                "metrics": [
                    {"columnId": "0", "id": "metrics/visitors"},
                    {"columnId": "1", "id": "metrics/pageviews"},
                ]
            },
            "dimension": "variables/daterangeday",
            "settings": {"limit": 20},
        }

        async with session.post(
            f"https://analytics.adobe.io/api/{auth.company_id}/reports",
            headers=headers,
            json=request_body,
        ) as response:
            logger.info(f"Response status: {response.status}")
            if response.status == 200:
                result = await response.json()
                logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                error_text = await response.text()
                logger.error(f"API 요청 실패: {error_text}")

    logger.info("테스트 완료")
    logger.info("종료합니다.")


async def main():
    await test_report_api()


if __name__ == "__main__":
    asyncio.run(main())
