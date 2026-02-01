"""
에어비앤비(airbnb.co.kr) 홈페이지 동적 크롤러
브라우저로 열고, 사용자가 원하는 페이지로 이동한 뒤 엔터 시 숙소 목록 수집
Edge 또는 Chrome 지원 (로봇 감지 완화 적용)
"""

import os
import re
import sys
import time

# exe로 실행 시 작업 폴더 = exe 위치, 아니면 스크립트 위치
if getattr(sys, "frozen", False):
    _PROJECT_DIR = os.path.dirname(sys.executable)
    os.chdir(_PROJECT_DIR)  # exe: 작업 폴더를 exe 위치로 (base_library.zip\.wdm 오류 방지)
else:
    _PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ChromeDriver/EdgeDriver 캐시를 exe(또는 스크립트) 폴더로만 사용 (base_library.zip\.wdm 오류 방지)
_WDM_CACHE = os.path.join(_PROJECT_DIR, "wdm_drivers")
os.makedirs(_WDM_CACHE, exist_ok=True)
os.environ["WDM_SSL_VERIFY"] = "0"
# exe 실행 시 WDM_LOCAL 설정 금지: WDM_LOCAL=1이면 webdriver_manager가 sys.path[0]/.wdm 사용 → PyInstaller에서 base_library.zip\.wdm 오류
if not getattr(sys, "frozen", False):
    os.environ["WDM_LOCAL"] = "1"
from datetime import datetime
from selenium import webdriver
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 사용할 브라우저: "edge" | "chrome"
BROWSER = "chrome"

# EdgeDriver 수동 경로 (필요 시 환경변수 EDGE_DRIVER_PATH 또는 여기 지정)
EDGE_DRIVER_PATH = os.environ.get("EDGE_DRIVER_PATH", "")

# Chrome 로봇 감지 우회 (undetected-chromedriver). exe 실행 시에는 비활성화(캐시 경로 오류 방지)
USE_UNDETECTED = False
if BROWSER == "chrome" and not getattr(sys, "frozen", False):
    try:
        import undetected_chromedriver as uc
        USE_UNDETECTED = True
    except ImportError:
        pass

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
try:
    from webdriver_manager.core.driver_cache import DriverCacheManager
    _WDM_CACHE_MANAGER = DriverCacheManager(_WDM_CACHE)
except Exception:
    _WDM_CACHE_MANAGER = None


# 에어비앤비 크롤링 대상
AIRBNB_HOME_URL = "https://www.airbnb.co.kr/homes"
AIRBNB_BASE = "https://www.airbnb.co.kr"

# 크롤링 최대 페이지 수 (1~3)
MAX_PAGES = 3

# 제공 HTML 구조 기준 (카드 내 data-testid 사용으로 정확·빠름)
LISTING_LINK_SELECTOR = 'a[href*="/rooms/"][aria-labelledby^="title_"]'
# 가격: 가격 전용 스타일만 사용 (속도 개선)
PRICE_ROW_SELECTOR = '[data-testid="price-availability-row"]'  # 카드 찾기용
PRICE_SPAN_STYLE = 'span[style*="pricing-guest-primary-line-unit-price"]'  # ₩159,765 전용
# 평점/리뷰: 동일 카드 내 span[aria-hidden="true"] 중 "4.87 (23)" 형태 또는 "평점 N점, 후기 N개" span
RATING_SPAN_ARIA_HIDDEN = 'span[aria-hidden="true"]'  # 텍스트 예: "5.0 (29)"
RATING_SPAN_CONTAINS = "평점"  # "평점 5.0점(5점 만점), 후기 29개"

# User-Agent
USER_AGENT_EDGE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
)
USER_AGENT_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# 로봇 감지 우회 CDP 스크립트
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: function() { return undefined; } });
Object.defineProperty(navigator, 'languages', { get: function() { return ['ko-KR', 'ko', 'en-US', 'en']; } });
window.chrome = window.chrome || { runtime: {} };
"""


def _apply_stealth(driver: WebDriver) -> None:
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": STEALTH_SCRIPT})
    except Exception:
        pass


def create_driver(headless: bool = False):
    """Edge 또는 Chrome 드라이버 생성"""
    if BROWSER == "edge":
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--lang=ko-KR")
        options.add_argument(f"--user-agent={USER_AGENT_EDGE}")
        options.add_experimental_option("useAutomationExtension", False)

        if EDGE_DRIVER_PATH and os.path.isfile(EDGE_DRIVER_PATH):
            service = EdgeService(executable_path=EDGE_DRIVER_PATH)
            driver = webdriver.Edge(service=service, options=options)
        else:
            try:
                if _WDM_CACHE_MANAGER is not None:
                    service = EdgeService(EdgeChromiumDriverManager(cache_manager=_WDM_CACHE_MANAGER).install())
                else:
                    service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)
            except Exception as e:
                if "Connection" in str(type(e).__name__) or "getaddrinfo" in str(e).lower():
                    print("EdgeDriver 자동 다운로드 실패. Selenium 내장 방식으로 시도...")
                driver = webdriver.Edge(options=options)
        _apply_stealth(driver)
    else:
        if USE_UNDETECTED:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--lang=ko-KR")
            options.add_argument(f"--user-agent={USER_AGENT_CHROME}")
            if headless:
                options.add_argument("--headless=new")
            driver = uc.Chrome(options=options, use_subprocess=True)
        else:
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_argument("--lang=ko-KR")
            options.add_argument(f"--user-agent={USER_AGENT_CHROME}")
            options.add_experimental_option("useAutomationExtension", False)
            if _WDM_CACHE_MANAGER is not None:
                service = ChromeService(ChromeDriverManager(cache_manager=_WDM_CACHE_MANAGER).install())
            else:
                service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            _apply_stealth(driver)
    driver.implicitly_wait(10)
    driver.set_window_size(1280, 900)
    return driver


def open_airbnb_page(driver: WebDriver) -> bool:
    """에어비앤비 홈(숙소 목록) 페이지로 이동"""
    driver.get(AIRBNB_HOME_URL)
    time.sleep(1.2)
    return True


def accept_cookie_if_any(driver: WebDriver) -> None:
    """쿠키/동의 팝업 버튼이 있으면 클릭"""
    selectors = [
        'button[data-testid="accept-cookie-banner"]',
        'button:contains("동의"), button:contains("Accept")',
        'a[href*="cookie"]',
        '[aria-label*="동의"], [aria-label*="Accept"]',
        'button[class*="accept"], button[class*="agree"]',
    ]
    for sel in selectors:
        try:
            if ":contains" in sel:
                continue
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
                break
        except Exception:
            continue


# 평점/리뷰 텍스트 패턴: "4.87 (23)" 또는 "5.0 (29)"
RATING_PATTERN = re.compile(r"^\d\.?\d*\s*\(\d+\)\s*$")
# 카드 내 평점 형태 검색용 (텍스트 일부에서 추출)
RATING_IN_TEXT = re.compile(r"\d\.?\d*\s*\(\d+\)")


def _get_card_container(link_el):
    """링크에 속한 카드 = price-availability-row를 포함하는 가장 가까운(좁은) 상위 컨테이너. 행 어긋남 방지."""
    try:
        el = link_el
        best = None
        for _ in range(15):
            try:
                parent = el.find_element(By.XPATH, "..")
            except Exception:
                break
            el = parent
            try:
                rows = el.find_elements(By.CSS_SELECTOR, PRICE_ROW_SELECTOR)
                if not rows:
                    continue
                # 카드 하나만 포함하는 조상 우선: 내부에 PRICE_ROW_SELECTOR가 1개인 것이 가장 좁은 카드
                if len(rows) == 1:
                    best = el
                elif best is None:
                    best = el
            except Exception:
                continue
        return best
    except Exception:
        pass
    return None


def _get_price_from_card(card) -> str:
    """카드 내 가격 추출. 총액 우선 → 전용 스타일 → ₩ 포함 span 순으로 fallback."""
    if not card:
        return ""
    try:
        # 1) 총액(총 가격) 우선: aria-label에 "총액" 포함된 span의 텍스트 사용
        for span in card.find_elements(By.CSS_SELECTOR, 'span[aria-label*="총액"]'):
            t = (span.text or "").strip()
            if t and "₩" in t and len(t) < 25:
                return t
        # aria-label에서 "총액 ₩X,XXX" 형태 직접 파싱 (텍스트가 비어있을 때)
        for span in card.find_elements(By.CSS_SELECTOR, 'span[aria-label*="총액"]'):
            label = (span.get_attribute("aria-label") or "").strip()
            m = re.search(r"총액\s*(₩[\d,]+)", label)
            if m:
                return m.group(1)
        # 2) 가격 전용 스타일 span
        for span in card.find_elements(By.CSS_SELECTOR, PRICE_SPAN_STYLE):
            t = (span.text or "").strip()
            if t and "₩" in t and len(t) < 25:
                return t
        # 3) ₩ 포함 span (짧은 텍스트만, 단위/설명 제외)
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            t = (span.text or "").strip()
            if t and "₩" in t and len(t) < 25 and "박" not in t and "요금" not in t:
                return t
        # 4) div 등 다른 요소에서 ₩ 포함 텍스트
        for el in card.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='Price']"):
            t = (el.text or "").strip()
            if t and "₩" in t and len(t) < 25:
                return t
    except Exception:
        pass
    return ""


def _get_rating_from_card(card) -> str:
    """카드 내 평점/리뷰 추출. '4.87 (23)' / '평점 N점, 후기 N개' 형태 여러 경로로 검색해 누락 최소화."""
    if not card:
        return ""
    try:
        # 1) aria-hidden="true" span 중 "4.87 (23)" 형태
        for span in card.find_elements(By.CSS_SELECTOR, RATING_SPAN_ARIA_HIDDEN):
            t = (span.text or "").strip()
            if RATING_PATTERN.match(t):
                return t
        # 2) "평점 N점, 후기 N개" 포함 span
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            t = (span.text or "").strip()
            if RATING_SPAN_CONTAINS in t and "후기" in t and len(t) < 80:
                return t
        # 3) 카드 전체 텍스트에서 "4.87 (23)" 패턴 검색 (후기 없는 신규 숙소는 제외되지만 누락 방지)
        full_text = (card.text or "").strip()
        m = RATING_IN_TEXT.search(full_text)
        if m:
            return m.group(0).strip()
        # 4) "점" + 숫자 + "후기" 형태
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            t = (span.text or "").strip()
            if "점" in t and "후기" in t and len(t) < 80:
                return t
    except Exception:
        pass
    return ""


def get_airbnb_listings(driver: WebDriver) -> list[dict]:
    """현재 페이지 숙소 수집 (제목·가격·평점·링크). data-testid 기반으로 정확·빠르게 추출."""
    results = []
    seen_links = set()

    try:
        link_els = driver.find_elements(By.CSS_SELECTOR, LISTING_LINK_SELECTOR)
    except Exception:
        link_els = []

    for link_el in link_els:
        try:
            # 지연 로딩된 가격/평점이 보이도록 해당 링크를 화면에 노출
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", link_el)
                time.sleep(0.05)
            except Exception:
                pass

            href = (link_el.get_attribute("href") or "").strip()
            if not href or "/rooms/" not in href:
                continue
            if href.startswith("/"):
                href = AIRBNB_BASE.rstrip("/") + href
            if href in seen_links:
                continue
            seen_links.add(href)

            title = ""
            title_id = link_el.get_attribute("aria-labelledby")
            if title_id:
                try:
                    title_el = driver.find_element(By.ID, title_id)
                    title = (title_el.text or "").strip()
                except Exception:
                    pass
            if not title:
                title = "(제목 없음)"

            card = _get_card_container(link_el)
            price = _get_price_from_card(card) if card else ""
            rating = _get_rating_from_card(card) if card else ""

            results.append({
                "title": title,
                "price": price or "",
                "rating": rating or "",
                "link": href,
            })
        except Exception:
            continue

    return results


def save_listings_to_excel(listings: list[dict], filepath: str | None = None) -> str:
    """수집된 숙소 목록을 엑셀 파일로 저장. 저장 경로 반환."""
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"airbnb_listings_{timestamp}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "숙소 목록"
    headers = ["번호", "제목", "가격", "평점/후기", "링크"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    for row, item in enumerate(listings, 2):
        ws.cell(row=row, column=1, value=row - 1)
        ws.cell(row=row, column=2, value=item.get("title", ""))
        ws.cell(row=row, column=3, value=item.get("price", ""))
        ws.cell(row=row, column=4, value=item.get("rating", ""))
        ws.cell(row=row, column=5, value=item.get("link", ""))
    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].width = 20
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["E"].width = 60
    wb.save(filepath)
    return filepath


def go_to_next_page(driver: WebDriver) -> bool:
    """다음 페이지로 이동 (다음 버튼 클릭 또는 URL 변경). 성공 시 True."""
    # 에어비앤비: 다음 버튼/링크 선택자 (여러 후보 시도)
    next_selectors = [
        ('css', 'a[aria-label="다음"]'),
        ('css', 'a[aria-label="Next"]'),
        ('css', '[data-testid="pagination-next"]'),
        ('css', 'a[href*="items_offset"]'),
        ('xpath', '//a[contains(@aria-label,"다음") or contains(@aria-label,"Next")]'),
        ('xpath', '//button[contains(text(),"다음") or contains(text(),"Next")]'),
    ]
    for kind, sel in next_selectors:
        try:
            by = By.CSS_SELECTOR if kind == "css" else By.XPATH
            el = driver.find_element(by, sel)
            if el.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.3)
                el.click()
                time.sleep(1.2)
                return True
        except Exception:
            continue
    return False


def main():
    driver = None
    try:
        print(f"{'Edge' if BROWSER == 'edge' else 'Chrome'} 브라우저 시작..." + (" (로봇 감지 우회)" if USE_UNDETECTED else ""))
        driver = create_driver(headless=False)
        time.sleep(1)

        print("에어비앤비 홈페이지 열기...")
        open_airbnb_page(driver)

        input("\n>>> 검색/필터 후 원하는 목록이 보이면, 여기 터미널에서 엔터를 누르면 크롤링을 시작합니다.\n")

        current_url = driver.current_url
        print(f"현재 페이지: {current_url[:90]}{'...' if len(current_url) > 90 else ''}\n")

        accept_cookie_if_any(driver)
        time.sleep(0.3)

        all_listings = []
        seen_links = set()

        for page_num in range(MAX_PAGES):
            print(f"숙소 목록 수집 중... ({page_num + 1}/{MAX_PAGES}페이지)")
            page_listings = get_airbnb_listings(driver)
            for item in page_listings:
                link = item.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_listings.append(item)
            if page_num < MAX_PAGES - 1 and not go_to_next_page(driver):
                print(f"다음 페이지가 없어 {page_num + 1}페이지까지 수집했습니다.")
                break
            time.sleep(1)

        if not all_listings:
            print("수집된 숙소가 없습니다. 페이지가 완전히 로드된 뒤 다시 엔터를 눌러 보세요.")
        else:
            print(f"\n수집된 숙소: {len(all_listings)}개 (최대 {MAX_PAGES}페이지)\n")
            for i, item in enumerate(all_listings, 1):
                print(f"[{i}] {item['title']}")
                if item.get("price"):
                    print(f"    가격: {item['price']}")
                if item.get("rating"):
                    print(f"    평점/후기: {item['rating']}")
                print(f"    링크: {item['link']}\n")

            excel_path = save_listings_to_excel(all_listings)
            print(f"엑셀 저장 완료: {excel_path}")

        input("엔터를 누르면 브라우저를 종료합니다...")
    finally:
        if driver:
            driver.quit()
            print("브라우저 종료됨.")


if __name__ == "__main__":
    main()
