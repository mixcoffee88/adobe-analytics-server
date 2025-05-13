# 1. Python 3.12 slim 기반 이미지
FROM python:3.12-slim

# 2. cryptography 등 일부 패키지를 위한 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 5. 전체 소스 복사
COPY . .

# 6. FastMCP 서버 실행 (예: server.py)
CMD ["python", "src/server.py"]
