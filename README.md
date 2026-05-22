# Privacy Safety Agent

사진 묶음(bundle)의 각 사진에서 개인정보·민감정보 신호를 탐지해 공개 산출물에서 제외할 사진을 분류하는 FastAPI 에이전트입니다.

## 역할

Momently 파이프라인에서 `photo_exif_llm_pipeline` 이후, 그룹화·네러티브 생성 단계 이전에 위치합니다.

- **소비**: `photo_exif_llm_pipeline`이 생성한 bundle의 `photos` 배열 (각 항목에 `photo_summary` 포함)
- **생산**: 사진을 `public_photos`와 `excluded_photos`로 분리하고 각 사진에 `privacy_review` 결과 첨부

## API

### `GET /health`

서비스 상태를 반환합니다.

**응답 예시**

```json
{ "status": "ok", "service": "privacy_safety_agent" }
```

---

### `POST /api/v1/privacy-safety`

사진 묶음에 대해 개인정보·민감정보 심사를 수행합니다.

**요청 본문**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `project_id` | string | 필수 | 프로젝트 식별자 (최소 1자) |
| `photos` | array | 선택 | 사진 객체 배열 (`photo_summary` 포함) |

**요청 예시**

```json
{
  "project_id": "trip-2024-seoul",
  "photos": [
    {
      "file_name": "passport_scan.jpg",
      "photo_summary": {
        "ocr_text": ["Call me at 010-1234-5678", "user@example.com"]
      }
    },
    {
      "file_name": "IMG_0001.jpg",
      "photo_summary": { "summary": "카페 내부 풍경" }
    }
  ]
}
```

**응답 예시**

```json
{
  "project_id": "trip-2024-seoul",
  "privacy_status": "ok",
  "public_photo_count": 1,
  "excluded_photo_count": 1,
  "public_photos": [
    {
      "file_name": "IMG_0001.jpg",
      "exclude_from_public_outputs": false,
      "privacy_review": { "public_safe": true, "signals": [], "policy": "allow" }
    }
  ],
  "excluded_photos": [
    {
      "file_name": "passport_scan.jpg",
      "exclude_from_public_outputs": true,
      "exclusion_reason": "sensitive_filename, phone, email",
      "privacy_review": {
        "public_safe": false,
        "signals": ["sensitive_filename", "phone", "email"],
        "policy": "exclude"
      }
    }
  ],
  "checks": [
    { "name": "metadata_flags", "status": "pass" },
    { "name": "filename_terms", "status": "pass" },
    { "name": "ocr_text_patterns", "status": "pass" }
  ]
}
```

**탐지 신호 종류**

| 신호 | 탐지 기준 |
|------|-----------|
| `pre_flagged_exclusion` | 사진 또는 `photo_summary`에 `exclude_from_public_outputs: true` 이미 설정 |
| `sensitive_filename` | 파일명에 `passport`, `license`, `idcard`, `resident`, `ssn`, `credit`, `card`, `receipt`, `ticket` 포함 |
| `sensitive_text_term` | OCR/summary 텍스트에 `주민등록`, `여권`, `운전면허`, `신용카드`, `계좌번호` 등 민감 키워드 포함 |
| `email` | OCR/summary에서 이메일 주소 패턴 감지 |
| `phone` | OCR/summary에서 전화번호 패턴 감지 |
| `credit_card_like` | OCR/summary에서 13~19자리 연속 숫자 패턴 감지 |
| `korean_rrn_like` | OCR/summary에서 주민등록번호 형식(`YYMMDD-N######`) 감지 |

심사는 결정론적으로 동작하며 LLM을 사용하지 않습니다.

## 실행

### 로컬

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api_server:app --reload --port 8081
```

### Docker

현재 Dockerfile이 없습니다. 컨테이너 배포는 orchestrator의 `docker-compose.yml`에서 관리합니다.

## 설정

환경 변수 없음. 모든 파라미터는 요청 본문으로 전달됩니다.

## 테스트

```bash
# 단위 테스트
python3 -m unittest discover -s tests -t .

# 커버리지 포함 표준 검증 (90% 이상 필요)
scripts/verify.sh

# PYTHON 환경 변수로 인터프리터 지정 시
PYTHON=/path/to/python scripts/verify.sh
```

## 구조

```text
privacy_safety_agent/
├── src/
│   ├── api_server.py      # FastAPI 앱, 엔드포인트 정의
│   └── privacy_guard.py   # 결정론적 민감정보 탐지 및 분류 순수 함수
├── tests/
│   └── test_privacy_safety_agent.py
├── scripts/
│   └── verify.sh          # 커버리지 게이트 포함 검증 스크립트
└── requirements.txt       # fastapi, uvicorn, pydantic, httpx, coverage
```
