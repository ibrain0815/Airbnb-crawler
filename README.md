# 에어비앤비 크롤러 개발 지침서

에어비앤비(airbnb.co.kr) 숙소 목록을 동적 크롤링하는 데스크톱 앱입니다.  
나중에 한 번에 개발·수정할 수 있도록 프로젝트 구조와 핵심 지침을 정리했습니다.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **기능** | 에어비앤비 홈페이지 → 검색/필터 후 숙소 목록(제목·가격·평점·링크) 수집 → 엑셀 저장 |
| **실행 방식** | GUI(tkinter) 또는 콘솔 |
| **브라우저** | Chrome(기본) 또는 Edge |
| **배포** | PyInstaller exe + Inno Setup 설치 파일 |

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
| `create_driver()` | Chrome/Edge WebDriver 생성 (Selenium, undetected-chromedriver 또는 webdriver-manager) |
| `open_airbnb_page()` | 에어비앤비 홈 URL로 이동 |
| `accept_cookie_if_any()` | 쿠키/동의 팝업 처리 |
| `_get_card_container()` | 링크 요소 → 해당 숙소 카드 DOM 찾기 |
| `_get_price_from_card()` | 카드 내 가격 추출 (총액 우선) |
| `_get_rating_from_card()` | 카드 내 평점/후기 추출 |
| `get_airbnb_listings()` | 현재 페이지 숙소 목록 수집 (제목·가격·평점·링크) |
| `go_to_next_page()` | 다음 페이지로 이동 |
| `save_listings_to_excel()` | 목록 → 엑셀 저장 |

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
| `LISTING_LINK_SELECTOR` | 숙소 링크 선택자 | `a[href*="/rooms/"][aria-labelledby^="title_"]` |
| `PRICE_ROW_SELECTOR` | 카드 찾기용 (가격 행 포함) | `[data-testid="price-availability-row"]` |
| `PRICE_SPAN_STYLE` | 가격 스타일 span | `span[style*="pricing-guest-primary-line-unit-price"]` |
| `RATING_SPAN_ARIA_HIDDEN` | 평점 span | `span[aria-hidden="true"]` |
| `RATING_SPAN_CONTAINS` | 평점 텍스트 키워드 | `"평점"` |

### 4.2 가격 추출 (`_get_price_from_card`)

**우선순위**

1. `span[aria-label*="총액"]` — 총액(총 가격) 표시
2. `aria-label`에서 `총액 ₩X,XXX` 정규식 파싱
3. `PRICE_SPAN_STYLE` span
4. `₩` 포함 span (짧은 텍스트)
5. `[class*='price']` / `[class*='Price']` 요소

**에어비앤비 예시**

```html
<span aria-label="총액 ₩194,000, 원래 요금 ₩241,488">₩194,000</span>
```

### 4.3 평점 추출 (`_get_rating_from_card`)

**우선순위**

1. `span[aria-hidden="true"]` 중 `"4.87 (23)"` 형태
2. `"평점 N점, 후기 N개"` 포함 span
3. 카드 전체 텍스트에서 `\d\.?\d*\s*\(\d+\)` 패턴 검색
4. `"점"` + `"후기"` 포함 span

### 4.4 다음 페이지 (`go_to_next_page`)

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
# GUI 실행 (배포용 진입점)
python gui_app.py

# 콘솔 실행 (디버깅용)
python main.py
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
| 가격/평점 누락 | `_get_price_from_card`, `_get_rating_from_card`에 fallback 추가, `_get_card_container`가 너무 넓은 부모를 잡지 않는지 확인 |
| 행 어긋남 | 카드는 "PRICE_ROW_SELECTOR가 1개인 가장 좁은 부모"로 한정 |
| `base_library.zip\.wdm` 오류 | exe 환경에서 `WDM_LOCAL` 비설정, `DriverCacheManager` 사용 |
| ChromeDriver 버전 문제 | exe와 같은 폴더 `wdm_drivers\.wdm`에 캐시됨. 삭제 후 재실행 시 재다운로드 |
| 로봇 감지 | exe에서는 undetected-chromedriver 비활성화. 스크립트 실행 시에만 `USE_UNDETECTED=True` 사용 가능 |

---

## 8. 수집 데이터 형식

| 필드 | 타입 | 예시 |
|------|------|------|
| `title` | str | "서울 강남 한적한 숙소" |
| `price` | str | "₩194,000" (총액) |
| `rating` | str | "4.87 (23)" 또는 "평점 5.0점(5점 만점), 후기 29개" |
| `link` | str | "https://www.airbnb.co.kr/rooms/12345678" |

엑셀 컬럼: 번호, 제목, 가격, 평점/후기, 링크

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

---

## 10. 참고

- **배포 상세**: `배포안내.txt`
- **의존성**: selenium, webdriver-manager, openpyxl, (선택) undetected-chromedriver, flask
