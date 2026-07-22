---
style: |
  img {
    display: block;
    float: none;
    margin-left: auto;
    margin-right: auto;
  }
marp: true
paginate: true
---
# 공공데이터포털 오픈 API 테스트
### 식품안전나라 - 건강기능식품 영양DB(I0760)

---
## 오늘의 학습 목표
- API 상세 페이지에서 요청/응답 구조를 읽을 수 있다.
- 인증키를 `.env`로 안전하게 관리할 수 있다.
- Python으로 오픈 API를 호출하고 결과를 데이터프레임으로 변환할 수 있다.
- 응답 결과 코드로 성공/실패를 판단할 수 있다.

---
## 실습 대상 API
> [식품안전나라 오픈API - 건강기능식품 영양DB(I0760)](https://www.foodsafetykorea.go.kr/api/openApiInfo.do?svc_no=I0760)

식품의약품안전처가 제공하는 **건강기능식품 항목과 분류 체계**(대·중·소분류 코드와 명칭)를 조회하는 API입니다.

- 서비스ID: `I0760`
- 응답 형식: XML / JSON
- 1회 호출 최대 1,000건
- 테스트용 `sample` 키 지원

---
## API 상세 페이지에서 먼저 볼 것
API를 호출하기 전, 문서에서 아래 항목부터 확인합니다.

| 항목 | 건강기능식품 영양DB(I0760) |
| --- | --- |
| 요청 주소 | `openapi.foodsafetykorea.go.kr/api/...` |
| 요청 파라미터 | 인증키, 서비스ID, 응답형식, 시작/종료위치 (+ 선택 조건) |
| 응답 항목 | 건강 항목 그룹, 대·중·소분류 코드와 명칭 |
| 인증 방식 | 인증키(API Key) 필요 |
| 호출 제한 | 1회 최대 1,000건 |

---
## 1. 요청 URL 구조
```
http://openapi.foodsafetykorea.go.kr/api/{인증키}/{서비스ID}/{요청타입}/{시작위치}/{종료위치}
```

조건을 추가할 때는 뒤에 `/키=값&키=값` 형태로 붙입니다.
```
.../{시작위치}/{종료위치}/HELT_ITM_GRP_NM=값
```

---
## 요청 파라미터
| 순서 | 이름 | 필수 | 설명 |
| --- | --- | --- | --- |
| 1 | 인증키 | O | 발급받은 API Key |
| 2 | 서비스ID | O | `I0760` (건강기능식품 영양DB) |
| 3 | 요청타입 | O | `xml` 또는 `json` |
| 4 | 시작위치 | O | 조회 시작 행 번호 |
| 5 | 종료위치 | O | 조회 종료 행 번호 |
| - | `HELT_ITM_GRP_NM` | X | 건강 항목 그룹 명으로 필터링 |

---
## 응답 항목 (주요 항목)
| 필드명 | 설명 |
| --- | --- |
| `HELT_ITM_GRP_CD` / `HELT_ITM_GRP_NM` | 건강 항목 그룹 코드 / 명 |
| `LCLAS_CD` / `LCLAS_NM` | 대분류 코드 / 명 |
| `MLSFC_CD` / `MLSFC_NM` | 중분류 코드 / 명 |
| `SCLAS_CD` / `SCLAS_NM` | 소분류 코드 / 명 |

> 전체 응답 항목은 API 상세 페이지의 "출력값(Response Message)" 표에서 확인합니다.

---
## 2. 인증키 준비하기
API를 호출하려면 인증키가 필요합니다.

1. 식품안전나라 홈페이지에서 인증키를 신청한다.
2. 이 폴더의 `.env.sample`을 복사해 `.env`를 만든다.
3. `FOOD_SAFETY_API_KEY` 값에 발급받은 키를 입력한다.

```
FOOD_SAFETY_API_KEY=발급받은_인증키
```

> 인증키 발급 절차는 [`공공데이터활용 - 인증키 생성.md`](./공공데이터활용%20-%20인증키%20생성.md) 참고

---
## 3. 코드로 호출하기 - 준비
```python
import os, json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FOOD_SAFETY_API_KEY")

if not API_KEY or API_KEY == "발급받은_인증키를_입력하세요":
    API_KEY = "sample"  # I0760에서 지원하는 테스트용 키
```

`.env`는 Git에 올리지 않고, `.env.sample`만 공유해서 팀원이 각자 키를 채워 넣게 합니다. 인증키가 담긴 URL도 노트북 출력이나 로그에 남기지 않습니다.

---
## 3. 코드로 호출하기 - 요청
```python
BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"
SERVICE_ID, DATA_TYPE = "I0760", "json"

url = f"{BASE_URL}/{API_KEY}/{SERVICE_ID}/{DATA_TYPE}/1/5"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.RequestException as error:
    # 기본 오류 메시지에 URL과 인증키가 노출되지 않도록 오류 유형만 알린다.
    raise RuntimeError(f"API 요청 실패: {type(error).__name__}") from None

data = response.json()
```

---
## 4. 응답 구조 확인하기
정상적인 JSON 응답은 `{서비스ID: {...}}` 형태입니다. HTTP 오류나 JSON이 아닌 응답은 먼저 예외로 처리해야 합니다.

```json
{
  "I0760": {
    "total_count": "12345",
    "row": [ { "HELT_ITM_GRP_NM": "프랑스해안송꺼질추출물", "LCLAS_NM": "건강기능식품", "...": "..." } ],
    "RESULT": { "CODE": "INFO-000", "MSG": "정상처리되었습니다." }
  }
}
```

먼저 `RESULT.CODE`로 성공 여부를 확인한 뒤 `row`를 사용합니다.

---
## 5. 데이터프레임으로 변환하기
```python
def call_food_api(service_id, api_key=API_KEY, data_type="json",
                   start_idx=1, end_idx=5, **params):
    url = f"{BASE_URL}/{api_key}/{service_id}/{data_type}/{start_idx}/{end_idx}"
    if params:
        url += "/" + "&".join(f"{k}={v}" for k, v in params.items())

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        # 인증키가 담긴 URL 대신 오류 유형만 알린다.
        raise RuntimeError(f"API 요청 실패: {type(error).__name__}") from None

    data = response.json()
    if service_id not in data:
        raise KeyError(f"응답에 서비스 ID '{service_id}'가 없습니다: {list(data)}")

    body = data[service_id]
    result = body["RESULT"]

    if result["CODE"] != "INFO-000":
        print(f"[{result['CODE']}] {result['MSG']}")
        return result["CODE"], pd.DataFrame()

    return result["CODE"], pd.DataFrame(body.get("row", []))
```

---
## 6. 조건 추가해서 검색하기
```python
code, df = call_food_api("I0760", end_idx=20)

if not df.empty:
    target_name = df.iloc[0]["HELT_ITM_GRP_NM"]
    code, df_target = call_food_api(
        "I0760", end_idx=50, HELT_ITM_GRP_NM=target_name
    )
```

- 응답에서 얻은 `HELT_ITM_GRP_NM` 값을 다음 요청의 조건으로 재사용합니다.
- 파라미터를 `**params`로 받아두면 다른 API에도 함수를 재사용할 수 있습니다.

---
## 7. 결과 코드로 상태 판단하기
| 코드 | 의미 |
| --- | --- |
| `INFO-000` | 정상 처리 |
| `INFO-200` | 해당 조건의 데이터 없음 |
| `INFO-100` | 인증키가 없거나 유효하지 않음 |
| `ERROR-300` | 필수 파라미터 누락 |
| `ERROR-336` | 요청 범위 초과 (최대 1,000건) |
| `ERROR-310` | 해당하는 서비스를 찾을 수 없음 |
| `ERROR-500` | 서버 오류 |

> `sample` 키의 지원 여부는 데이터셋마다 다릅니다. 건강기능식품 영양DB(I0760)는 `sample` 키로 실습할 수 있습니다.


---
## 정리
- API 문서는 **요청 URL, 파라미터, 응답 항목, 인증 방식, 호출 제한**을 중심으로 읽는다.
- 인증키는 코드에 직접 적지 않고 `.env`로 분리해서 관리한다.
- 응답은 `RESULT.CODE`로 먼저 성공 여부를 확인한 뒤 데이터를 사용한다.
- 하나의 호출 함수를 만들어두면 다른 공공데이터 API에도 재사용할 수 있다.
