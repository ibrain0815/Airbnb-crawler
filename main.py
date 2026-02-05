"""
ìì´ë¹ì¤ë¹(airbnb.co.kr) ííì´ì§ ëì  í¬ë¡¤ë¬
ë¸ë¼ì°ì ë¡ ì´ê³ , ì¬ì©ìê° ìíë íì´ì§ë¡ ì´ëí ë¤ ìì ëª©ë¡ ìì§
Edge ëë Chrome ì§ì (ë¡ë´ ê°ì§ ìí ì ì©)

ì¤í: python main.py â ë²í¼ì´ ìë GUI ì°½ì´ ë¹ëë¤.
     python main.py --console â í°ë¯¸ë ì ì© ëª¨ë.
"""

import os
import re
import sys
import time

# exeë¡ ì¤í ì ìì í´ë = exe ìì¹, ìëë©´ ì¤í¬ë¦½í¸ ìì¹
if getattr(sys, "frozen", False):
    _PROJECT_DIR = os.path.dirname(sys.executable)
    os.chdir(_PROJECT_DIR)  # exe: ìì í´ëë¥¼ exe ìì¹ë¡ (base_library.zip\.wdm ì¤ë¥ ë°©ì§)
else:
    _PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ChromeDriver/EdgeDriver ìºìë¥¼ exe(ëë ì¤í¬ë¦½í¸) í´ëë¡ë§ ì¬ì© (base_library.zip\.wdm ì¤ë¥ ë°©ì§)
_WDM_CACHE = os.path.join(_PROJECT_DIR, "wdm_drivers")
os.makedirs(_WDM_CACHE, exist_ok=True)
os.environ["WDM_SSL_VERIFY"] = "0"
# exe ì¤í ì WDM_LOCAL ì¤ì  ê¸ì§: WDM_LOCAL=1ì´ë©´ webdriver_managerê° sys.path[0]/.wdm ì¬ì© â PyInstallerìì base_library.zip\.wdm ì¤ë¥
if not getattr(sys, "frozen", False):
    os.environ["WDM_LOCAL"] = "1"
from datetime import datetime
from selenium import webdriver
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ì¬ì©í  ë¸ë¼ì°ì : "edge" | "chrome"
BROWSER = "chrome"

# EdgeDriver ìë ê²½ë¡ (íì ì íê²½ë³ì EDGE_DRIVER_PATH ëë ì¬ê¸° ì§ì )
EDGE_DRIVER_PATH = os.environ.get("EDGE_DRIVER_PATH", "")

# Chrome ë¡ë´ ê°ì§ ì°í (undetected-chromedriver). exe ì¤í ììë ë¹íì±í(ìºì ê²½ë¡ ì¤ë¥ ë°©ì§)
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


# ìì´ë¹ì¤ë¹ í¬ë¡¤ë§ ëì
AIRBNB_HOME_URL = "https://www.airbnb.co.kr/homes"
AIRBNB_BASE = "https://www.airbnb.co.kr"

# í¬ë¡¤ë§ ìµë íì´ì§ ì (1~3)
MAX_PAGES = 3

# ë¸ë¼ì°ì /ëë¼ì´ë² (ìëÂ·ë´ ê°ì§ ê· í)
IMPLICIT_WAIT_SEC = 3
WINDOW_SIZE = (1920, 1080)
# ì§ì° ìê° (ë´ ê°ì§ ì°í, ë¬¸ì ê¶ì¥ ë²ì ë´)
DELAY_FIRST_PAGE_SEC = 2.0
DELAY_NEXT_PAGE_AFTER_CLICK_SEC = 1.0
DELAY_BETWEEN_PAGES_SEC = 1.0

# ì ê³µ HTML êµ¬ì¡° ê¸°ì¤ (ì¹´ë ë´ data-testid ì¬ì©ì¼ë¡ ì íÂ·ë¹ ë¦)
LISTING_LINK_SELECTOR = 'a[href*="/rooms/"][aria-labelledby^="title_"]'
# ê°ê²©: ê°ê²© ì ì© ì¤íì¼ë§ ì¬ì© (ìë ê°ì )
PRICE_ROW_SELECTOR = '[data-testid="price-availability-row"]'  # ì¹´ë ì°¾ê¸°ì©
PRICE_SPAN_STYLE = 'span[style*="pricing-guest-primary-line-unit-price"]'  # â©159,765 ì ì©
# íì /ë¦¬ë·°: ëì¼ ì¹´ë ë´ span[aria-hidden="true"] ì¤ "4.87 (23)" íí ëë "íì  Nì , íê¸° Nê°" span
RATING_SPAN_ARIA_HIDDEN = 'span[aria-hidden="true"]'  # íì¤í¸ ì: "5.0 (29)"
RATING_SPAN_CONTAINS = "íì "  # "íì  5.0ì (5ì  ë§ì ), íê¸° 29ê°"
# ì£¼ì/ìì¹
ADDRESS_SELECTORS = [
    '[data-testid="listing-card-subtitle"]',
    '[data-testid="listing-card-location"]',
]

# ê³ ì ìì§: execute_script 1íë¡ ì¹´ë ì ì²´ ìì§ (íì´ì§ë¹ 1ë² ìë³µ)
_FAST_SCRAPE_SCRIPT = """
var base = "https://www.airbnb.co.kr";
var links = document.querySelectorAll('a[href*="/rooms/"][aria-labelledby^="title_"]');
var out = [], seen = {};
for (var i = 0; i < links.length; i++) {
  var a = links[i];
  var href = (a.getAttribute("href") || "").trim();
  if (!href || href.indexOf("/rooms/") === -1) continue;
  if (href.charAt(0) === "/") href = base + href;
  if (seen[href]) continue;
  seen[href] = true;
  var title = "";
  var tid = a.getAttribute("aria-labelledby");
  if (tid) {
    var te = document.getElementById(tid);
    if (te) title = (te.textContent || "").trim();
  }
  var card = null, el = a;
  for (var up = 0; up < 20 && el; up++) {
    el = el.parentElement;
    if (!el) break;
    var tid = el.getAttribute("data-testid");
    if (tid === "listing-card") { card = el; break; }
    if (tid === "card-container") { card = el; break; }
  }
  if (!card) {
    el = a;
    for (var up = 0; up < 20 && el; up++) {
      el = el.parentElement;
      if (!el) break;
      var rows = el.querySelectorAll('[data-testid="price-availability-row"]');
      if (rows.length === 1) { card = el; break; }
      if (rows.length > 1 && !card) card = el;
    }
  }
  if (!title && card) {
    var titleEl = card.querySelector('[data-testid="listing-card-title"]') || card.querySelector("h2");
    if (titleEl) title = (titleEl.textContent || "").trim();
  }
  if (!title) title = "(ììëª ìì)";
  var price = "", rating = "", address = "";
  function onlyTotalAmount(str) {
    if (!str || str.indexOf("â©") === -1) return "";
    var m = str.match(/ì´ì¡\\s*(â©[\\d,]+)/);
    if (m) return m[1];
    if (str.indexOf("ìë ìê¸") !== -1) {
      var before = str.split("ìë ìê¸")[0].trim();
      m = before.match(/â©[\\d,]+/);
      return m ? m[0] : "";
    }
    m = str.match(/â©[\\d,]+/);
    return m ? m[0] : "";
  }
  if (card) {
    var ps = card.querySelectorAll('[data-testid="price-availability-row"] span[aria-label*="ì´ì¡"]');
    for (var j = 0; j < ps.length; j++) {
      var label = (ps[j].getAttribute("aria-label") || "").trim();
      if (label) { price = onlyTotalAmount(label); if (price) break; }
      var txt = (ps[j].textContent || "").trim();
      if (/^â©[\\d,]+$/.test(txt)) { price = txt; break; }
    }
    if (!price) {
      ps = card.querySelectorAll('span[aria-label*="ì´ì¡"]');
      for (var j = 0; j < ps.length; j++) {
        var label = (ps[j].getAttribute("aria-label") || "").trim();
        if (label) { price = onlyTotalAmount(label); if (price) break; }
      }
    }
    if (!price) {
      var prow = card.querySelector('[data-testid="price-availability-row"]');
      if (prow) {
        var spans = prow.querySelectorAll("span");
        for (var j = 0; j < spans.length; j++) {
          var lbl = (spans[j].getAttribute("aria-label") || "").trim();
          var txt = (spans[j].textContent || "").trim();
          if (/^â©[\\d,]+$/.test(txt)) {
            if (lbl.indexOf("ìë ìê¸") !== -1 && onlyTotalAmount(lbl) === "") continue;
            price = txt; break;
          }
          price = onlyTotalAmount(lbl || txt);
          if (price) break;
        }
      }
    }
    if (!price) {
      var sp = card.querySelectorAll('span[style*="pricing-guest-primary-line-unit-price"]');
      for (var j = 0; j < sp.length; j++) {
        var txt = (sp[j].textContent || "").trim();
        if (/^â©[\\d,]+$/.test(txt)) { price = txt; break; }
      }
    }
    if (!price) {
      var u = card.querySelector("span.u174bpcy");
      if (u) {
        var txt = (u.textContent || "").trim();
        if (/^â©[\\d,]+$/.test(txt)) price = txt;
      }
    }
    var rs = card.querySelectorAll('.t1phmnpa span[aria-hidden="true"]');
    for (var j = 0; j < rs.length; j++) {
      t = (rs[j].textContent || "").trim();
      if (/^\\d\\.?\\d*\\s*\\(\\d+\\)\\s*$/.test(t)) { rating = t; break; }
    }
    if (!rating) {
      rs = card.querySelectorAll("span.a8jt5op");
      for (var j = 0; j < rs.length; j++) {
        t = (rs[j].textContent || "").trim();
        if (t && t.length < 30) { rating = t; break; }
      }
    }
    if (!rating) {
      rs = card.querySelectorAll('span[aria-hidden="true"]');
      for (var j = 0; j < rs.length; j++) {
        t = (rs[j].textContent || "").trim();
        if (/^\\d\\.?\\d*\\s*\\(\\d+\\)\\s*$/.test(t)) { rating = t; break; }
      }
    }
    if (!rating) {
      var all = card.querySelectorAll("span");
      for (var j = 0; j < all.length; j++) {
        t = (all[j].textContent || "").trim();
        if (t.indexOf("íì ") !== -1 && t.indexOf("íê¸°") !== -1 && t.length < 80) { rating = t; break; }
      }
    }
    if (card) {
      var parts = [];
      var subs = card.querySelectorAll('[data-testid="listing-card-subtitle"]');
      for (var j = 0; j < subs.length; j++) {
        var pt = (subs[j].textContent || "").trim();
        if (pt) parts.push(pt);
      }
      if (parts.length) address = parts.join(" | ");
      if (!address) {
        var loc = card.querySelector('[data-testid="listing-card-location"]');
        if (loc) address = (loc.textContent || "").trim();
      }
    }
    if (!address) {
      el = a;
      for (var up = 0; up < 20 && el; up++) {
        el = el.parentElement;
        if (!el) break;
        var parts2 = [];
        var subs2 = el.querySelectorAll('[data-testid="listing-card-subtitle"]');
        for (var j = 0; j < subs2.length; j++) {
          var pt = (subs2[j].textContent || "").trim();
          if (pt) parts2.push(pt);
        }
        if (parts2.length) { address = parts2.join(" | "); break; }
        var loc = el.querySelector('[data-testid="listing-card-location"]');
        if (loc) { address = (loc.textContent || "").trim(); break; }
      }
    }
  }
  price = (price || "").replace(/,\s*$/, "");
  out.push({ title: title, price: price, rating: rating, address: address || "", link: href });
}
return out;
"""

# User-Agent
USER_AGENT_EDGE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
)
USER_AGENT_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# ë¡ë´ ê°ì§ ì°í CDP ì¤í¬ë¦½í¸
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
    """Edge ëë Chrome ëë¼ì´ë² ìì±"""
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
                    print("EdgeDriver ìë ë¤ì´ë¡ë ì¤í¨. Selenium ë´ì¥ ë°©ìì¼ë¡ ìë...")
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
    driver.implicitly_wait(IMPLICIT_WAIT_SEC)
    driver.set_window_size(WINDOW_SIZE[0], WINDOW_SIZE[1])
    return driver


def open_airbnb_page(driver: WebDriver) -> bool:
    """ìì´ë¹ì¤ë¹ í(ìì ëª©ë¡) íì´ì§ë¡ ì´ë"""
    driver.get(AIRBNB_HOME_URL)
    time.sleep(DELAY_FIRST_PAGE_SEC)
    return True


def accept_cookie_if_any(driver: WebDriver) -> None:
    """ì¿ í¤/ëì íì ë²í¼ì´ ìì¼ë©´ í´ë¦­"""
    selectors = [
        'button[data-testid="accept-cookie-banner"]',
        'button:contains("ëì"), button:contains("Accept")',
        'a[href*="cookie"]',
        '[aria-label*="ëì"], [aria-label*="Accept"]',
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


# íì /ë¦¬ë·° íì¤í¸ í¨í´: "4.87 (23)" ëë "5.0 (29)"
RATING_PATTERN = re.compile(r"^\d\.?\d*\s*\(\d+\)\s*$")
# ì¹´ë ë´ íì  íí ê²ìì© (íì¤í¸ ì¼ë¶ìì ì¶ì¶)
RATING_IN_TEXT = re.compile(r"\d\.?\d*\s*\(\d+\)")


def _get_card_container(link_el):
    """ë§í¬ì ìí ì¹´ë. listing-card â card-container â price-availability-row í¬í¨ ì¡°ì."""
    try:
        el = link_el
        for _ in range(20):
            try:
                parent = el.find_element(By.XPATH, "..")
            except Exception:
                break
            el = parent
            try:
                tid = (el.get_attribute("data-testid") or "").strip()
                if tid == "listing-card" or tid == "card-container":
                    return el
            except Exception:
                pass
        el = link_el
        best = None
        for _ in range(20):
            try:
                parent = el.find_element(By.XPATH, "..")
            except Exception:
                break
            el = parent
            try:
                rows = el.find_elements(By.CSS_SELECTOR, PRICE_ROW_SELECTOR)
                if not rows:
                    continue
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


# ê°ê²©: aria-label/íì¤í¸ìì ì´ì¡(ì²« ë²ì§¸ â©ì«ì)ë§ ì¶ì¶
_PRICE_TOTAL_PATTERN = re.compile(r"ì´ì¡\s*(â©[\d,]+)")
_PRICE_AMOUNT_ONLY = re.compile(r"^â©[\d,]+$")
_PRICE_FIRST_AMOUNT = re.compile(r"â©[\d,]+")


def _price_only_total(raw: str) -> str:
    """ì´ì¡/ì¤ì  íì ê¸ì¡ë§. 'ì´ì¡ â©1,155,213, ìë ìê¸ â©1,264,913'â'â©1,155,213'. 'â©679,000 Â· 5ë°, ìë ìê¸ â©920,957'â'â©679,000'(ìë ìê¸ ì ê¸ì¡)."""
    if not raw or "â©" not in raw:
        return ""
    s = (raw or "").strip().rstrip(",").strip()
    m = _PRICE_TOTAL_PATTERN.search(s)
    if m:
        return m.group(1).strip()
    if "ìë ìê¸" in s:
        before = s.split("ìë ìê¸")[0].strip()
        m = _PRICE_FIRST_AMOUNT.search(before)
        return m.group(0).strip() if m else ""
    if _PRICE_AMOUNT_ONLY.match(s):
        return s
    m = _PRICE_FIRST_AMOUNT.search(s)
    return m.group(0) if m else ""


def _get_price_from_card(card) -> str:
    """ì¹´ë ë´ ê°ê²© ì¶ì¶. ì´ì¡(â©ì«ì)ë§ ë°í. aria-label ì´ì¡ ì°ì  â price-row â u174bpcy/ì¤íì¼ span."""
    if not card:
        return ""
    try:
        # 1) price-availability-row ë´ span[aria-label*="ì´ì¡"] â ì´ì¡ë§
        try:
            row = card.find_element(By.CSS_SELECTOR, PRICE_ROW_SELECTOR)
            for span in row.find_elements(By.CSS_SELECTOR, 'span[aria-label*="ì´ì¡"]'):
                label = (span.get_attribute("aria-label") or "").strip()
                if label:
                    p = _price_only_total(label)
                    if p:
                        return p
                txt = (span.text or "").strip()
                if _PRICE_AMOUNT_ONLY.match(txt):
                    return txt
            for span in row.find_elements(By.CSS_SELECTOR, "span"):
                txt = (span.text or "").strip()
                if _PRICE_AMOUNT_ONLY.match(txt):
                    label = (span.get_attribute("aria-label") or "").strip()
                    if "ìë ìê¸" in label and not _price_only_total(label):
                        continue
                    return txt
        except Exception:
            pass
        # 2) ì¹´ë ì ì²´ span[aria-label*="ì´ì¡"] â ì´ì¡ë§
        for span in card.find_elements(By.CSS_SELECTOR, 'span[aria-label*="ì´ì¡"]'):
            label = (span.get_attribute("aria-label") or "").strip()
            if label:
                p = _price_only_total(label)
                if p:
                    return p
            txt = (span.text or "").strip()
            if _PRICE_AMOUNT_ONLY.match(txt):
                return txt
        # 3) span.u174bpcy / ì¤íì¼ span â íì¤í¸ê° â©ì«ìë§ ì¼ ëë§
        for span in card.find_elements(By.CSS_SELECTOR, "span[class*='u174bpcy']"):
            txt = (span.text or "").strip().rstrip(",").strip()
            if _PRICE_AMOUNT_ONLY.match(txt):
                return txt
        for span in card.find_elements(By.CSS_SELECTOR, PRICE_SPAN_STYLE):
            txt = (span.text or "").strip().rstrip(",").strip()
            if _PRICE_AMOUNT_ONLY.match(txt):
                return txt
        # 4) ê·¸ ì¸ â© í¬í¨ span (ìë ìê¸ë§ ìë span ì ì¸, 'ìë ìê¸' ì ê¸ì¡ ëë span íì¤í¸ ì¬ì©)
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            txt = (span.text or "").strip()
            if _PRICE_AMOUNT_ONLY.match(txt):
                label = (span.get_attribute("aria-label") or "").strip()
                if "ìë ìê¸" in label and not _price_only_total(label):
                    continue
                return txt
        for el in card.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='Price']"):
            txt = (el.text or "").strip()
            if _PRICE_AMOUNT_ONLY.match(txt):
                label = (el.get_attribute("aria-label") or "").strip()
                if "ìë ìê¸" in label and not _price_only_total(label):
                    continue
                return txt
    except Exception:
        pass
    return ""


def _get_rating_from_card(card) -> str:
    """ì¹´ë ë´ íì /ë¦¬ë·° ì¶ì¶. .t1phmnpa span[aria-hidden], span.a8jt5op(ì°¸ê³  í) â aria-hidden â íì /íê¸° íì¤í¸."""
    if not card:
        return ""
    try:
        # 1) .t1phmnpa span[aria-hidden="true"] (ì°¸ê³  í)
        for span in card.find_elements(By.CSS_SELECTOR, ".t1phmnpa span[aria-hidden='true']"):
            t = (span.text or "").strip()
            if RATING_PATTERN.match(t):
                return t
        # 2) span.a8jt5op (ì°¸ê³  í)
        for span in card.find_elements(By.CSS_SELECTOR, "span[class*='a8jt5op']"):
            t = (span.text or "").strip()
            if t and len(t) < 30:
                return t
        # 3) aria-hidden="true" span ì¤ "4.87 (23)" íí
        for span in card.find_elements(By.CSS_SELECTOR, RATING_SPAN_ARIA_HIDDEN):
            t = (span.text or "").strip()
            if RATING_PATTERN.match(t):
                return t
        # 4) "íì  Nì , íê¸° Nê°" í¬í¨ span
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            t = (span.text or "").strip()
            if RATING_SPAN_CONTAINS in t and "íê¸°" in t and len(t) < 80:
                return t
        # 5) ì¹´ë ì ì²´ íì¤í¸ìì "4.87 (23)" í¨í´ ê²ì
        full_text = (card.text or "").strip()
        m = RATING_IN_TEXT.search(full_text)
        if m:
            return m.group(0).strip()
        # 6) "ì " + "íê¸°" íí
        for span in card.find_elements(By.CSS_SELECTOR, "span"):
            t = (span.text or "").strip()
            if "ì " in t and "íê¸°" in t and len(t) < 80:
                return t
    except Exception:
        pass
    return ""


def _get_address_from_element(container) -> str:
    """ì»¨íì´ë ë´ ì£¼ì/ìì¹. ëª¨ë  listing-card-subtitle íì¤í¸ í©ì¹¨(íì íì) â listing-card-location."""
    if not container:
        return ""
    try:
        parts = []
        for el in container.find_elements(By.CSS_SELECTOR, '[data-testid="listing-card-subtitle"]'):
            t = (el.text or "").strip()
            if t:
                parts.append(t)
        if parts:
            return " | ".join(parts)
        for sel in ADDRESS_SELECTORS:
            try:
                el = container.find_element(By.CSS_SELECTOR, sel)
                t = (el.text or "").strip()
                if t:
                    return t
            except Exception:
                continue
    except Exception:
        pass
    return ""


def _get_address_from_card(card) -> str:
    """ì¹´ë ë´ ì£¼ì/ìì¹ ì¶ì¶. listing-card-subtitle â listing-card-location ì."""
    return _get_address_from_element(card)


def _get_address_near_link(link_el) -> str:
    """ë§í¬ì ì¡°ììì ì£¼ì/ìì¹ ìì íì (ì¹´ëê° ì¢ì ë ëë½ ë°©ì§)."""
    try:
        el = link_el
        for _ in range(20):
            try:
                parent = el.find_element(By.XPATH, "..")
            except Exception:
                break
            el = parent
            t = _get_address_from_element(el)
            if t:
                return t
    except Exception:
        pass
    return ""


# ìì¸ íì´ì§ ì§ë ë§ì»¤ìì ì¢í(ìë, ê²½ë) ì¶ì¶ì© í¨í´
_COORD_POSITION_PATTERN = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$")


def _extract_coords_from_position(position: str) -> tuple[str, str]:
    """gmp-advanced-marker position ë¬¸ìì´('35.163,129.1585')ìì ìëÂ·ê²½ëë§ ë¶ë¦¬."""
    if not position:
        return "", ""
    m = _COORD_POSITION_PATTERN.match(position.strip())
    if not m:
        return "", ""
    return m.group(1), m.group(2)


def get_listing_coordinates(driver: WebDriver, timeout: float = 5.0) -> tuple[str, str]:
    """ìì¸ íì´ì§ìì gmp-advanced-marker[position] ììë¡ ì¢í(ìë,ê²½ë) ì¶ì¶."""
    elems: list[WebDriver] = []
    try:
        elems = WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "gmp-advanced-marker[position]")
        )
    except Exception:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, "gmp-advanced-marker[position]")
        except Exception:
            elems = []
    for el in elems:
        try:
            pos = (el.get_attribute("position") or "").strip()
            lat, lng = _extract_coords_from_position(pos)
            if lat and lng:
                return lat, lng
        except Exception:
            continue
    return "", ""


def enrich_listings_with_coordinates(
    driver: WebDriver,
    listings: list[dict],
    max_items: int | None = None,
) -> int:
    """ê° ìì ë§í¬ ìì¸ íì´ì§ìì ì¢íë¥¼ ìì§í´ listingsì lat/lng íëë¥¼ ì¶ê°. ì±ê³µ ê°ì ë°í."""
    count = 0
    for item in listings:
        if max_items is not None and count >= max_items:
            break
        if item.get("lat") and item.get("lng"):
            continue
        link = (item.get("link") or "").strip()
        if not link:
            continue
        try:
            driver.get(link)
            # ìì¸ íì´ì§ ë¡ë© ì¬ì 
            time.sleep(1.0)
            lat, lng = get_listing_coordinates(driver)
            if lat and lng:
                item["lat"] = lat
                item["lng"] = lng
                count += 1
        except Exception:
            continue
    return count


def get_airbnb_listings(driver: WebDriver) -> list[dict]:
    """íì¬ íì´ì§ ìì ìì§. ê³ ì ìì§(execute_script 1í) ì°ì , ì¤í¨ ì SELECTORS fallback."""
    # ê³ ì ìì§: 1í ì¤í¬ë¦½í¸ë¡ ì ì²´ ì¹´ë ë°í (íì´ì§ë¹ 1ë² ìë³µ)
    try:
        raw = driver.execute_script(_FAST_SCRAPE_SCRIPT)
        if raw and isinstance(raw, list) and len(raw) > 0:
            return [
                {
                    "title": (x.get("title") or "").strip() or "(ììëª ìì)",
                    "price": (x.get("price") or "").strip().rstrip(",").strip(),
                    "rating": (x.get("rating") or "").strip(),
                    "address": (x.get("address") or "").strip(),
                    "link": (x.get("link") or "").strip(),
                }
                for x in raw
                if (x.get("link") or "").strip()
            ]
    except Exception:
        pass

    # Fallback: SELECTORSë¡ ì¹´ëÂ·ì ëª©Â·ê°ê²©Â·íì  ììë³ ìì§
    results = []
    seen_links = set()
    try:
        link_els = driver.find_elements(By.CSS_SELECTOR, LISTING_LINK_SELECTOR)
    except Exception:
        link_els = []

    for link_el in link_els:
        try:
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
            card = _get_card_container(link_el)
            if not title and card:
                try:
                    for sel in ['[data-testid="listing-card-title"]', "h2"]:
                        try:
                            title_el = card.find_element(By.CSS_SELECTOR, sel)
                            title = (title_el.text or "").strip()
                            if title:
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
            if not title:
                title = "(ììëª ìì)"

            price = _get_price_from_card(card) if card else ""
            price = (price or "").strip().rstrip(",").strip()
            rating = _get_rating_from_card(card) if card else ""
            address = _get_address_from_card(card) if card else ""
            if not address:
                address = _get_address_near_link(link_el)

            results.append({
                "title": title,
                "price": price,
                "rating": rating or "",
                "address": address or "",
                "link": href,
            })
        except Exception:
            continue

    return results


def save_listings_to_excel(listings: list[dict], filepath: str | None = None) -> str:
    """ìì§ë ìì ëª©ë¡ì ìì íì¼ë¡ ì ì¥. ì ì¥ ê²½ë¡ ë°í."""
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"airbnb_listings_{timestamp}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "ìì ëª©ë¡"
    headers = ["ë²í¸", "ììëª", "ê°ê²©", "íì /íê¸°", "ì£¼ì/ìì¹", "ìë", "ê²½ë", "ë§í¬"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    for row, item in enumerate(listings, 2):
        ws.cell(row=row, column=1, value=row - 1)
        ws.cell(row=row, column=2, value=item.get("title", ""))
        ws.cell(row=row, column=3, value=item.get("price", ""))
        ws.cell(row=row, column=4, value=item.get("rating", ""))
        ws.cell(row=row, column=5, value=item.get("address", ""))
        ws.cell(row=row, column=6, value=item.get("lat", ""))
        ws.cell(row=row, column=7, value=item.get("lng", ""))
        ws.cell(row=row, column=8, value=item.get("link", ""))
    for col in range(1, 9):
        ws.column_dimensions[get_column_letter(col)].width = 20
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["E"].width = 30
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["H"].width = 60
    # ì²« í ê³ ì  (ì¤í¬ë¡¤ ì í¤ë ê³ ì )
    ws.freeze_panes = "A2"
    # ëª¨ë  ì ê°ì´ë° ì ë ¬
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    last_row = len(listings) + 1
    for row in range(1, last_row + 1):
        for col in range(1, 9):
            ws.cell(row=row, column=col).alignment = center
    wb.save(filepath)
    return filepath


def go_to_next_page(driver: WebDriver) -> bool:
    """ë¤ì íì´ì§ë¡ ì´ë (ë¤ì ë²í¼ í´ë¦­ ëë URL ë³ê²½). ì±ê³µ ì True."""
    # ìì´ë¹ì¤ë¹: ë¤ì ë²í¼/ë§í¬ ì íì (ì¬ë¬ íë³´ ìë)
    next_selectors = [
        ('css', 'a[aria-label="ë¤ì"]'),
        ('css', 'a[aria-label="Next"]'),
        ('css', '[data-testid="pagination-next"]'),
        ('css', 'a[href*="items_offset"]'),
        ('xpath', '//a[contains(@aria-label,"ë¤ì") or contains(@aria-label,"Next")]'),
        ('xpath', '//button[contains(text(),"ë¤ì") or contains(text(),"Next")]'),
    ]
    for kind, sel in next_selectors:
        try:
            by = By.CSS_SELECTOR if kind == "css" else By.XPATH
            el = driver.find_element(by, sel)
            if el.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.2)
                el.click()
                time.sleep(DELAY_NEXT_PAGE_AFTER_CLICK_SEC)
                return True
        except Exception:
            continue
    return False


def main():
    driver = None
    try:
        print(f"{'Edge' if BROWSER == 'edge' else 'Chrome'} ë¸ë¼ì°ì  ìì..." + (" (ë¡ë´ ê°ì§ ì°í)" if USE_UNDETECTED else ""))
        driver = create_driver(headless=False)
        time.sleep(1)

        print("ìì´ë¹ì¤ë¹ ííì´ì§ ì´ê¸°...")
        open_airbnb_page(driver)

        input("\n>>> ê²ì/íí° í ìíë ëª©ë¡ì´ ë³´ì´ë©´, ì¬ê¸° í°ë¯¸ëìì ìí°ë¥¼ ëë¥´ë©´ í¬ë¡¤ë§ì ììí©ëë¤.\n")

        current_url = driver.current_url
        print(f"íì¬ íì´ì§: {current_url[:90]}{'...' if len(current_url) > 90 else ''}\n")

        accept_cookie_if_any(driver)
        time.sleep(0.3)

        all_listings = []
        seen_links = set()

        for page_num in range(MAX_PAGES):
            print(f"ìì ëª©ë¡ ìì§ ì¤... ({page_num + 1}/{MAX_PAGES}íì´ì§)")
            page_listings = get_airbnb_listings(driver)
            for item in page_listings:
                link = item.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_listings.append(item)
            if page_num < MAX_PAGES - 1 and not go_to_next_page(driver):
                print(f"ë¤ì íì´ì§ê° ìì´ {page_num + 1}íì´ì§ê¹ì§ ìì§íìµëë¤.")
                break
            time.sleep(DELAY_BETWEEN_PAGES_SEC)

        if not all_listings:
            print("ìì§ë ììê° ììµëë¤. íì´ì§ê° ìì í ë¡ëë ë¤ ë¤ì ìí°ë¥¼ ëë¬ ë³´ì¸ì.")
        else:
            print(f"\nìì§ë ìì: {len(all_listings)}ê° (ìµë {MAX_PAGES}íì´ì§)\n")

            # ìì¸ íì´ì§ìì ì¢í(ìëÂ·ê²½ë) ì¶ê° ìì§
            try:
                print("ìì ì¢í(ìëÂ·ê²½ë) ìì§ ì¤... (ìì¸ íì´ì§ ë°©ë¬¸)")
                added = enrich_listings_with_coordinates(driver, all_listings)
                print(f"ì¢íê° ì¶ê°ë ìì: {added}ê°\n")
            except Exception as e:
                print(f"ì¢í ìì§ ì¤ ì¤ë¥ ë°ì: {e}\n")

            for i, item in enumerate(all_listings, 1):
                print(f"[{i}] {item['title']}")
                if item.get("price"):
                    print(f"    ê°ê²©: {item['price']}")
                if item.get("rating"):
                    print(f"    íì /íê¸°: {item['rating']}")
                if item.get("address"):
                    print(f"    ì£¼ì/ìì¹: {item['address']}")
                if item.get("lat") and item.get("lng"):
                    print(f"    ì¢í: {item['lat']}, {item['lng']}")
                print(f"    ë§í¬: {item['link']}\n")

            excel_path = save_listings_to_excel(all_listings)
            print(f"ìì ì ì¥ ìë£: {excel_path}")

        input("ìí°ë¥¼ ëë¥´ë©´ ë¸ë¼ì°ì ë¥¼ ì¢ë£í©ëë¤...")
    finally:
        if driver:
            driver.quit()
            print("ë¸ë¼ì°ì  ì¢ë£ë¨.")


if __name__ == "__main__":
    # í¬ë¡¤ë§ ë²í¼ì´ ìë GUI ì¤í (ì½ìë§ ì°ë ¤ë©´: python main.py --console)
    if "--console" not in sys.argv:
        try:
            import gui_app
            gui_app.main()
        except Exception as e:
            print(f"\nGUI ì¤ë¥: {e}")
            import traceback
            traceback.print_exc()
            input("\nìí°ë¥¼ ëë¥´ë©´ ì¢ë£í©ëë¤...")
    else:
        try:
            main()
        except Exception as e:
            print(f"\nì¤ë¥ ë°ì: {e}")
            import traceback
            traceback.print_exc()
            input("\nìí°ë¥¼ ëë¥´ë©´ ì¢ë£í©ëë¤...")
