# 에어비앤비 크롤러 개발 지침서

에어비앤비(airbnb.co.kr) 숙소 목록을 동적 크롤링하는 데스크톱 앱입니다.  
나중에 한 번에 개발·수정할 수 있도록 프로젝트 구조와 핵심 지침을 정리했습니다.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **기능** | 에어비앤비 홈페이지 → 검색/필터 후 숙소 목록(숙소명·가격·평점·주소/위치·링크) 수집 → 엑셀 저장 |
| **실행 방식** | `python main.py` → GUI 기본, `python main.py --console` → 터미널 전용. 또는 `python gui_app.py` |
| **브라우저** | Chrome(기본) 또는 Edge |
| **배포** | PyInstaller exe + Inno Setup 설치 파일 |
| **크롤링 속도** | 고속 수집(execute_script 1회/페이지) 우선, 실패 시 SELECTORS fallback |

---

## 2. 프로젝트 구조

```
RealEstate/
├── main.py              # 크롤링 핵심 로직 (브라우저, 수집, 엑셀)
├── gui_app.py           # tkinter 데스크톱 GUI (진입점)
├── app.py               # Flask 웹 UI (선택 사용)
├── templates/           # Flask 템플릿
├── requirements.txt     # 실행 시 의존성
├── requirements-build.txt   # 빌드 시 의존성 (pyinstaller)
├── build_exe.spec       # PyInstaller 설정
├── build.bat            # exe 빌드 스크립트
├── AirbnbCrawler.iss    # Inno Setup 설치 파일 스크립트
├── build_installer.bat  # 설치 파일 빌드 스크립트
├── dist/                # 빌드 결과 (AirbnbCrawler.exe)
├── output/              # 설치 파일 결과 (AirbnbCrawler_Setup.exe)
└── wdm_drivers/         # ChromeDriver/EdgeDriver 캐시 (실행 시 자동 생성)
```

---

## 3. 핵심 파일 역할

### `main.py` — 크롤링 엔진

| 함수/상수 | 역할 |
|-----------|------|
| `create_driver()` | Chrome/Edge WebDriver 생성 (implicitly_wait 3초, 창 1920×1080) |
| `open_airbnb_page()` | 에어비앤비 홈 URL로 이동 |
| `accept_cookie_if_any()` | 쿠키/동의 팝업 처리 |
| `_get_card_container()` | 링크 → 카드 DOM (listing-card → card-container → price-availability-row 포함 조상) |
| `_get_price_from_card()` | 카드 내 **총액만** 추출 (₩숫자, 끝 쉼표 제거) |
| `_get_rating_from_card()` | 카드 내 평점 (표시 형식 "5.0 (9)" 우선) |
| `_get_address_from_element()` / `_get_address_from_card()` / `_get_address_near_link()` | 주소/위치 (모든 subtitle 합침, 조상 fallback) |
| `get_airbnb_listings()` | 고속 수집(`_FAST_SCRAPE_SCRIPT` 1회) 우선 → 실패 시 SELECTORS fallback (제목·가격·평점·주소·링크) |
| `go_to_next_page()` | 다음 페이지로 이동 |
| `save_listings_to_excel()` | 목록 → 엑셀 저장 (첫 행 고정, 가운데 정렬) |

### `gui_app.py` — GUI

- `CrawlerGUI`: tkinter 창, 3버튼(홈페이지 접속 / 크롤링 시작 / 엑셀 저장)
- `main` 모듈 지연 로드: `_get_main()` → `import main`
- 작업 스레드로 크롤링 실행 → GUI 멈춤 방지

---

## 4. 에어비앤비 DOM 구조 & 수정 포인트

에어비앤비 HTML이 바뀌면 아래 선택자/로직을 우선 점검·수정하세요.

### 4.1 상수 (main.py 상단)

| 상수 | 용도 | 예시 값 |
|------|------|---------|
| `AIRBNB_HOME_URL` | 초기 접속 URL | `https://www.airbnb.co.kr/homes` |
| `IMPLICIT_WAIT_SEC` | 요소 대기(초) | `3` |
| `WINDOW_SIZE` | 브라우저 창 크기 | `(1920, 1080)` |
| `DELAY_FIRST_PAGE_SEC`, `DELAY_NEXT_PAGE_AFTER_CLICK_SEC`, `DELAY_BETWEEN_PAGES_SEC` | 봇 감지 우회 지연 | `2.0`, `1.0`, `1.0` |
| `LISTING_LINK_SELECTOR` | 숙소 링크 선택자 | `a[href*="/rooms/"][aria-labelledby^="title_"]` |
| `PRICE_ROW_SELECTOR` | 카드 찾기용 (가격 행 포함) | `[data-testid="price-availability-row"]` |
| `PRICE_SPAN_STYLE` | 가격 스타일 span | `span[style*="pricing-guest-primary-line-unit-price"]` |
| `RATING_SPAN_ARIA_HIDDEN` | 평점 span | `span[aria-hidden="true"]` |
| `RATING_SPAN_CONTAINS` | 평점 텍스트 키워드 | `"평점"` |
| `ADDRESS_SELECTORS` | 주소/위치 선택자 목록 | `[data-testid="listing-card-subtitle"]`, `[data-testid="listing-card-location"]` |

### 4.1.1 크롤러 선택자 참고 표 (우선 → fallback)

| 키 | 용도 | 예시 선택자 |
|----|------|-------------|
| `listing_card` | 숙소 카드 컨테이너 | `[data-testid="listing-card"]`, `[data-testid="card-container"]`, `[data-testid="price-availability-row"]` 포함 조상 |
| `title` | 숙소명 | `[id^="title_"]`(aria-labelledby), `[data-testid="listing-card-title"]`, `h2` |
| `price` | 가격(총액만) | `[data-testid="price-availability-row"] span[aria-label*="총액"]`, `span.u174bpcy`, 스타일 span |
| `rating` | 평점/후기 | `.t1phmnpa span[aria-hidden="true"]`("5.0 (9)"), `span.a8jt5op`, "평점 N점, 후기 N개" |
| `address_location` | 주소/위치 | `[data-testid="listing-card-subtitle"]`(전체 합침), `[data-testid="listing-card-location"]` |
| `next_page` | 다음 페이지 | `a[aria-label*="다음"]`, `a[aria-label*="Next"]`, `a[href*="items_offset"]` |

### 4.2 카드 컨테이너 (`_get_card_container`)

**탐색 순서** (링크에서 부모로 올라가며)

1. `data-testid="listing-card"`
2. `data-testid="card-container"` (실제 목록 페이지에서 카드 래퍼로 자주 사용)
3. `[data-testid="price-availability-row"]`가 정확히 1개인 가장 좁은 조상

카드가 너무 좁으면 가격/평점/주소가 카드 밖에 있어 누락되므로, `card-container` 인식이 중요합니다.

### 4.3 가격 추출 (`_get_price_from_card`, `_price_only_total`)

**규칙**: **총액/실제 표시 금액(₩숫자)만** 저장. 원래 요금은 사용하지 않습니다.

- **총액이 있는 경우**: `aria-label` "총액 ₩1,155,213, 원래 요금 ₩1,264,913" → 정규식 `총액\s*(₩[\d,]+)` 로 **₩1,155,213**만 사용. 끝 쉼표 제거.
- **원래 요금이 있는 경우**: 라벨에서 **"원래 요금" 앞부분**에 나오는 금액만 사용.  
  - `"₩679,000 · 5박, 원래 요금 ₩920,957"` → **₩679,000** (표시 금액).  
  - `"원래 요금 ₩920,957"`만 있는 span은 **제외** (해당 span의 금액은 사용 안 함).
- span의 **표시 텍스트**가 `^₩[\d,]+$`일 때는 그대로 사용하되, 라벨에 "원래 요금"만 있고 앞에 금액이 없으면 그 span은 건너뜀.

**우선순위**

1. `[data-testid="price-availability-row"]` 내 `span[aria-label*="총액"]` → `_price_only_total(label)` (총액 regex 또는 원래 요금 앞 금액)
2. 카드 전체 `span[aria-label*="총액"]`
3. `span[class*='u174bpcy']`, `PRICE_SPAN_STYLE` span (텍스트가 `^₩[\d,]+$` 형태일 때만)
4. 그 외 `₩` 포함 span 중 단일 금액 형태 (원래 요금만 있는 span 제외)

**에어비앤비 예시**

```html
<span aria-label="총액 ₩929,831, 원래 요금 ₩1,017,031">₩929,831</span>
<span aria-label="₩679,000 · 5박, 원래 요금 ₩920,957">₩679,000</span>
<span class="u174bpcy" style="--pricing-guest-primary-line-unit-price...">₩605,965</span>
```
→ 저장값: `₩929,831`(총액), `₩679,000`(원래 요금 앞/표시 금액), `₩605,965` (쉼표 제거)

### 4.4 평점 추출 (`_get_rating_from_card`)

**표시 형식 우선**: 화면에 보이는 **"5.0 (9)"** 형식을 우선 사용합니다.

**우선순위**

1. `.t1phmnpa span[aria-hidden="true"]` 중 `"5.0 (9)"` 형태
2. `span[class*='a8jt5op']` (짧은 텍스트)
3. `span[aria-hidden="true"]` 중 `"4.87 (23)"` 형태
4. `"평점 N점, 후기 N개"` 포함 span
5. 카드 전체 텍스트에서 `\d\.?\d*\s*\(\d+\)` 패턴 검색
6. `"점"` + `"후기"` 포함 span

### 4.5 주소/위치 (`_get_address_from_element`, `_get_address_near_link`)

- **카드 내**: `[data-testid="listing-card-subtitle"]`를 **전부** 찾아 텍스트를 `" | "`로 이어 붙임. (여러 줄: "동글하우스", "도보 6분", "3월 2일~7일" 등)
- **없을 때**: `[data-testid="listing-card-location"]` 사용.
- **여전히 없을 때**: 링크의 조상 요소를 올라가며 같은 방식으로 subtitle/location 검색 (카드가 좁을 때 누락 방지).

### 4.6 고속 수집 (`_FAST_SCRAPE_SCRIPT`)

- `get_airbnb_listings()`에서 **페이지당 1회** `driver.execute_script(_FAST_SCRAPE_SCRIPT)`로 카드 전체를 JS에서 수집해 반환.
- 실패하거나 결과가 없으면 기존처럼 SELECTORS로 요소별 수집(fallback).
- DOM 구조 변경 시 위 참고 표와 `_FAST_SCRAPE_SCRIPT` 내 선택자를 함께 점검하세요.

### 4.7 다음 페이지 (`go_to_next_page`)

**시도하는 선택자**

- `a[aria-label="다음"]`, `a[aria-label="Next"]`
- `[data-testid="pagination-next"]`
- `a[href*="items_offset"]`

에어비앤비 페이지네이션 구조 변경 시 위 선택자들을 업데이트하세요.

---

## 5. 개발 워크플로우

### 5.1 환경 설정

```bash
# 가상환경 권장
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 5.2 실행

```bash
# 기본: GUI 실행 (main.py가 gui_app 호출)
python main.py

# 터미널 전용 (엔터로 크롤링 시작/종료)
python main.py --console

# GUI만 직접 실행
python gui_app.py
```

### 5.3 DOM 구조 변경 시 작업 순서

1. 브라우저 개발자 도구로 실제 DOM 확인
2. `main.py` 상단 상수 수정 (선택자 등)
3. `_get_price_from_card`, `_get_rating_from_card` fallback 로직 검토
4. 필요 시 `_get_card_container` 로직 조정 (카드 경계 정의)
5. `python gui_app.py` 또는 `python main.py`로 검증

---

## 6. 배포 절차

### 6.1 exe 빌드

```bash
# build.bat 실행 또는
pip install -r requirements-build.txt
pyinstaller --noconfirm build_exe.spec
```

→ `dist\AirbnbCrawler.exe` 생성

### 6.2 설치 파일 빌드

1. [Inno Setup](https://jrsoftware.org/isinfo.php) 설치
2. `build_installer.bat` 실행

→ `output\AirbnbCrawler_Setup.exe` 생성

### 6.3 PyInstaller 수정 시

- `build_exe.spec`의 `hiddenimports`에 `main` 등 필수 모듈 유지
- exe 빌드 시 `base_library.zip\.wdm` 오류가 나면:
  - `main.py`에서 exe 실행 시 `WDM_LOCAL` 미설정
  - `DriverCacheManager(_WDM_CACHE)`를 Chrome/Edge 모두에 전달

---

## 7. 주의사항 및 트러블슈팅

| 상황 | 대응 |
|------|------|
| 가격/평점/주소 누락 | 카드가 `card-container`/`listing-card`로 잡히는지 확인. `_get_card_container`에 `card-container` 포함. 주소는 모든 subtitle 합침 + 조상 fallback |
| 행 어긋남 | 카드는 listing-card → card-container → PRICE_ROW_SELECTOR 1개인 가장 좁은 부모 순으로 탐색 |
| `base_library.zip\.wdm` 오류 | exe 환경에서 `WDM_LOCAL` 비설정, `DriverCacheManager` 사용 |
| ChromeDriver 버전 문제 | exe와 같은 폴더 `wdm_drivers\.wdm`에 캐시됨. 삭제 후 재실행 시 재다운로드 |
| 로봇 감지 | exe에서는 undetected-chromedriver 비활성화. 스크립트 실행 시에만 `USE_UNDETECTED=True` 사용 가능 |

---

## 8. 수집 데이터 형식

| 필드 | 타입 | 예시 |
|------|------|------|
| `title` | str | "부산의 집" (숙소명) |
| `price` | str | "₩605,965" (총액만, 끝 쉼표 없음) |
| `rating` | str | "5.0 (9)" 또는 "평점 5.0점(5점 만점), 후기 9개" |
| `address` | str | "동글하우스 \| 도보 6분 \| 3월 2일~7일" (subtitle 전체 합침) |
| `link` | str | "https://www.airbnb.co.kr/rooms/12345678" |

**엑셀**: 번호, **숙소명**, 가격, 평점/후기, **주소/위치**, 링크 — 첫 행 고정, 셀 가운데 정렬.

---

## 9. 개발 이력 — 프롬프트 순서

이 프로젝트를 처음부터 만들기 위해 지시한 프롬프트를 순서대로 정리했습니다.

### 9.1 초기 크롤러 개발

1. **"네이버 부동산 웹사이트에서 아파트 단지 정보를 크롤링하는 Python 프로그램을 만들어줘. 동적 크롤링과 버튼 클릭 기능을 포함해줘."**
   - Selenium 기반 동적 크롤링 구조 생성
   - `main.py`, `requirements.txt` 초기 작성

2. **URL 변경 및 XPath 기반 크롤링**
   - 네이버 부동산 → 에어비앤비로 타겟 변경
   - XPath 기반 요소 선택 추가

3. **로봇 감지 우회**
   - `undetected-chromedriver` 도입
   - User-Agent 설정, CDP 스텔스 스크립트 추가

### 9.2 브라우저 및 드라이버 설정

4. **"Edge 브라우저 사용하고 싶어"**
   - Edge 지원 추가 (`BROWSER` 상수)
   - EdgeChromiumDriverManager 설정

5. **EdgeDriver 다운로드 오류 해결**
   - `webdriver-manager` 캐시 경로 설정
   - 수동 EdgeDriver 경로 지원

### 9.3 에어비앤비 크롤링 전환

6. **사용자 입력 기반 크롤링**
   - 에어비앤비 홈으로 접속 후 사용자가 검색/필터 → 엔터 시 크롤링 시작

7. **에어비앤비 숙소 목록 크롤링**
   - `get_airbnb_listings()` 함수 작성
   - 제목, 링크, 가격, 평점 추출

### 9.4 크롤링 정확도 개선

8. **크롤링 속도 개선 및 평점/가격 추출 정확도 향상**
   - 카드 컨테이너 효율적 탐색
   - 가격 전용 스타일 span 사용
   - 평점 "X.X (N)" 형식 우선 추출

9. **최대 크롤링 페이지 수 설정**
   - GUI에 Spinbox 추가 (1~20 페이지)

10. **엑셀 저장 기능**
    - `openpyxl` 사용
    - `save_listings_to_excel()` 함수 추가

### 9.5 GUI 및 배포

11. **데스크톱 GUI 개발**
    - Flask 대신 tkinter 사용
    - `gui_app.py` 생성 (3버튼: 홈페이지 접속 / 크롤링 시작 / 엑셀 저장)

12. **PyInstaller exe 빌드**
    - `build_exe.spec`, `build.bat` 작성
    - `hiddenimports`에 `main` 모듈 추가

### 9.6 exe 실행 오류 해결

13. **"오류: [WinError 3] 지정된 경로를 찾을 수 없습니다: base_library.zip\\.wdm"**
    - exe 실행 시 `WDM_LOCAL` 미설정으로 변경
    - `DriverCacheManager`를 Chrome/Edge 모두에 전달
    - exe 실행 시 undetected-chromedriver 비활성화

### 9.7 데이터 품질 개선

14. **"가격과 평점이 빠져있는데 누락되지 않도록 개선해줘"**
    - `_get_card_container()` 개선: 가장 좁은 카드만 선택
    - 가격/평점 추출에 여러 fallback 추가
    - 링크를 화면에 스크롤해 지연 로딩 대응

15. **"가격 금액은 총액의 가격을 표시해줘"**
    - `span[aria-label*="총액"]` 우선 추출
    - 원래 요금이 아닌 총액만 표시

### 9.8 설치 파일 생성

16. **"설치 파일도 만들어줘"**
    - Inno Setup 스크립트 작성 (`AirbnbCrawler.iss`)
    - `build_installer.bat` 생성
    - 바탕화면 바로가기, 제거 프로그램 포함

### 9.9 문서화

17. **"에어비엔비 개발 기능을 나중에 한번에 개발할수 있도록 지침서를 readme.md파일로 만들어줘"**
    - 프로젝트 구조, 핵심 함수, DOM 선택자 정리
    - 개발 워크플로우, 배포 절차, 트러블슈팅 작성

18. **"에어비엔비 크롤링을 만들기 위해 지시내린 프롬프트를 README.md에 순서대로 정리해줘"**
    - 이 섹션 작성

### 9.10 추가 개발 (인터페이스·속도·데이터 품질)

19. **실행 시 GUI 미표시**
    - `main.py` 실행 시 기본 진입을 GUI로 변경 (`import gui_app` → `gui_app.main()`). 터미널 전용은 `python main.py --console`.

20. **크롤링 속도 개선**
    - 브라우저/지연: `implicitly_wait` 10→3초, 창 1280×900→1920×1080, 첫 페이지/다음 페이지/페이지 간 지연 상수화(`DELAY_*`).
    - 고속 수집: `_FAST_SCRAPE_SCRIPT` 추가 — `execute_script` 1회로 페이지 전체 카드 수집, 실패 시 기존 요소별 fallback.

21. **엑셀·레이블 정리**
    - 가격 끝 쉼표 제거. 엑셀 헤더 "제목"→"숙소명", "(제목 없음)"→"(숙소명 없음)".
    - 엑셀: 첫 행 고정(`freeze_panes`), 모든 셀 가운데 정렬(`Alignment`).

22. **주소/위치 수집**
    - `[data-testid="listing-card-subtitle"]`, `[data-testid="listing-card-location"]` 수집.
    - 엑셀에 "주소/위치" 컬럼 추가. 고속 스크립트·fallback·조상 탐색(`_get_address_near_link`) 모두 반영.

23. **가격: 총액만 추출**
    - `aria-label` "총액 ₩929,831, 원래 요금 …"에서 총액만 파싱. `span.u174bpcy` 등은 `^₩[\d,]+$` 형태일 때만 사용. `_price_only_total()` 도입.

24. **가격: 원래 요금 제외·표시 금액 우선**
    - "원래 요금"만 있는 라벨(예: "원래 요금 ₩1,264,913")은 사용하지 않음. 해당 span은 건너뜀.
    - "원래 요금"이 있는 라벨에서 **"원래 요금" 앞**에 나오는 금액만 사용. 예: `"₩679,000 · 5박, 원래 요금 ₩920,957"` → ₩679,000. span 표시 텍스트(₩679,000)도 동일하게 사용.

25. **카드·주소·평점 누락 방지**
    - 카드 탐색에 `data-testid="card-container"` 추가 (listing-card → card-container → price-availability-row).
    - 주소: 카드 내 **모든** `listing-card-subtitle` 텍스트를 `" | "`로 합침. 조상에서도 동일 방식 fallback.
    - 평점: `.t1phmnpa span[aria-hidden="true"]`로 표시 형식 "5.0 (9)" 우선. 참고 표 선택자 반영.

26. **README 업데이트**
    - 실행 방식, 상수, 선택자 참고 표, 카드/가격/평점/주소/고속 수집 설명, 수집 데이터 형식(주소·엑셀), 트러블슈팅, 개발 이력(19~26) 반영.

---

## 10. 참고

- **배포 상세**: `배포안내.txt`
- **의존성**: selenium, webdriver-manager, openpyxl, (선택) undetected-chromedriver, flask
