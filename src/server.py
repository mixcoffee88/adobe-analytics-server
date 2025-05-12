import asyncio
import logging
import os
import sys
from mcp.server.fastmcp import FastMCP
from auth.adobe_auth import AdobeAuth
from tools.get_report import GetReportTool
from tools.get_dimensions import GetDimensionsTool
from tools.get_metrics import GetMetricsTool
from tools.get_segments import GetSegmentsTool
from tools.get_calculated_metrics import GetCalculatedMetricsTool
from tools.get_report_suites import GetReportSuitesTool
from tools.get_realtime_report import GetRealtimeReportTool
from tools.get_data_feeds import GetDataFeedsTool

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP 서버 인스턴스 생성
mcp = FastMCP(
    name="adobe-analytics-server",
    description="당신은 Adobe Analytics API와 상호작용하는 분석 도우미입니다. 리포트 스위트 ID, 날짜 범위, 지표, 차원 등의 매개변수를 기반으로 보고서, 지표, 실시간 데이터를 조회할 수 있습니다."
    " 또한 사용 가능한 차원, 지표, 세그먼트, 계산된 지표 목록을 가져올 수 있습니다."
    " 이 도구는 Adobe Analytics API와 통신하여 데이터를 가져오고, 이를 기반으로 다양한 분석 작업을 수행할 수 있습니다."
    "get_report,get_realtime_report을 호출하기전에  get_dimensions,get_metrics을 호출하여 사용 가능한 차원과 지표 목록을 확인할 수 있습니다."
    "get_report_suites를 호출하여 사용 가능한 리포트 스위트 목록을 가져올 수 있습니다."
    "get_segments를 호출하여 사용 가능한 세그먼트 목록을 가져올 수 있습니다."
    "get_calculated_metrics를 호출하여 사용 가능한 계산된 지표 목록을 가져올 수 있습니다."
    "get_data_feeds를 호출하여 사용 가능한 데이터 피드 목록을 가져올 수 있습니다.",
    tools=[
        GetReportTool,
        GetDimensionsTool,
        GetMetricsTool,
        GetSegmentsTool,
        GetCalculatedMetricsTool,
        GetReportSuitesTool,
        GetRealtimeReportTool,
        GetDataFeedsTool,
    ],
    host="0.0.0.0",
    port=80,
)

# 환경 변수에서 RSID 가져오기
REPORT_SUITE_ID = os.getenv("REPORT_SUITE_ID")
if not REPORT_SUITE_ID:
    raise ValueError("REPORT_SUITE_ID 환경 변수가 설정되지 않았습니다.")


def get_report_suite_id(params: dict) -> str:
    """파라미터에서 리포트 스위트 ID를 가져오거나 환경 변수에서 가져옵니다.
    기본적으로는 환경 변수에서 가져오며, 파라미터에 rsid가 명시적으로 지정된 경우에만 파라미터 값을 사용합니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 명시적으로 지정된 리포트 스위트 ID
    """
    # 파라미터에 rsid가 명시적으로 지정된 경우에만 파라미터 값 사용
    if "rsid" in params and params["rsid"]:
        return params["rsid"]

    return REPORT_SUITE_ID


@mcp.tool()
async def get_report(params: dict) -> dict:
    """Adobe Analytics 리포트를 가져옵니다.

    Args:
        params (dict): 리포트 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - date_range (str): 날짜 범위
            - metrics (list): 지표 목록
            - dimension (str, optional): 차원
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_report : ", params)
    auth = AdobeAuth()
    tool = GetReportTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    return await tool.execute(params)


@mcp.tool()
async def get_dimensions(params: dict) -> dict:
    """사용 가능한 차원 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_dimensions : ", params)
    auth = AdobeAuth()
    tool = GetDimensionsTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    return await tool.execute(params)


@mcp.tool()
async def get_metrics(params: dict) -> dict:
    """사용 가능한 지표 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - limit (int, optional): 결과 제한 수 (기본값: 10)
            - page (int, optional): 페이지 번호 (기본값: 0)
            - max_results (int, optional): 최대 결과 수 (기본값: 20)
    """
    logger.info("get_metrics : ", params)
    auth = AdobeAuth()
    tool = GetMetricsTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    # 기본 제한값 설정 (더 적은 양의 데이터)
    if "limit" not in params:
        params["limit"] = 10
    if "max_results" not in params:
        params["max_results"] = 20

    logger.info(
        f"Metrics 요청 시작: limit={params.get('limit')}, max_results={params.get('max_results')}"
    )
    result = await tool.execute(params)
    logger.info(f"Metrics 요청 완료: {len(result.get('content', []))}개 항목 반환")

    return result


@mcp.tool()
async def get_segments(params: dict) -> dict:
    """사용 가능한 세그먼트 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_segments : ", params)
    auth = AdobeAuth()
    tool = GetSegmentsTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    return await tool.execute(params)


@mcp.tool()
async def get_calculated_metrics(params: dict) -> dict:
    """사용 가능한 계산된 지표 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_calculated_metrics : ", params)
    auth = AdobeAuth()
    tool = GetCalculatedMetricsTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    return await tool.execute(params)


@mcp.tool()
async def get_report_suites(params: dict) -> dict:
    """사용 가능한 리포트 스위트 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_report_suites : ", params)
    auth = AdobeAuth()
    tool = GetReportSuitesTool(auth)
    return await tool.execute(params)


@mcp.tool()
async def get_realtime_report(params: dict) -> dict:
    """실시간 리포트를 가져옵니다.

    Args:
        params (dict): 파라미터
            - rsid (str, optional): 리포트 스위트 ID. 없으면 환경 변수에서 가져옵니다.
            - metrics (list): 지표 목록
            - dimension (str, optional): 차원
            - limit (int, optional): 결과 제한 수
    """
    logger.info("get_realtime_report : ", params)
    auth = AdobeAuth()
    tool = GetRealtimeReportTool(auth)

    # 리포트 스위트 ID 설정
    params["rsid"] = get_report_suite_id(params)

    return await tool.execute(params)


@mcp.tool()
async def get_data_feeds(params: dict) -> dict:
    """데이터 피드 목록을 가져옵니다.

    Args:
        params (dict): 파라미터
            - limit (int, optional): 결과 제한 수
            - page (int, optional): 페이지 번호
    """
    logger.info("get_data_feeds : ", params)
    auth = AdobeAuth()
    tool = GetDataFeedsTool(auth)
    return await tool.execute(params)


if __name__ == "__main__":
    try:
        logger.info("Initializing server...")
        mcp.run(transport="sse")
        logger.info("Server started and connected successfully")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}", exc_info=True)
        sys.exit(1)
