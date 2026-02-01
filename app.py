"""
크롤링 웹 인터페이스 (Flask)
- 홈페이지 접속 / 크롤링 시작 / 엑셀 저장 API
"""

import os
import time
from flask import Flask, render_template, jsonify, request, send_file

# main 모듈에서 크롤러 함수 사용
from main import (
    create_driver,
    open_airbnb_page,
    get_airbnb_listings,
    save_listings_to_excel,
    go_to_next_page,
    accept_cookie_if_any,
    MAX_PAGES,
)

app = Flask(__name__)

# 전역: 브라우저 드라이버와 수집 결과 (단일 스레드 기준)
_driver = None
_listings = []


def _get_driver():
    global _driver
    return _driver


def _set_driver(d):
    global _driver
    _driver = d


def _get_listings():
    global _listings
    return _listings


def _set_listings(lst):
    global _listings
    _listings = lst


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/open-homepage", methods=["POST"])
def api_open_homepage():
    """에어비앤비 홈페이지를 브라우저로 열기."""
    try:
        driver = _get_driver()
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            _set_driver(None)
        time.sleep(0.5)
        driver = create_driver(headless=False)
        _set_driver(driver)
        time.sleep(1)
        open_airbnb_page(driver)
        return jsonify({"ok": True, "message": "에어비앤비 홈페이지를 열었습니다. 검색/필터 후 크롤링 시작을 누르세요."})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/start-crawl", methods=["POST"])
def api_start_crawl():
    """현재 브라우저 페이지에서 숙소 목록 크롤링 (최대 MAX_PAGES 페이지)."""
    driver = _get_driver()
    if not driver:
        return jsonify({"ok": False, "message": "먼저 '홈페이지 접속'을 눌러 주세요."}), 400
    try:
        accept_cookie_if_any(driver)
        time.sleep(0.3)
        all_listings = []
        seen_links = set()
        for page_num in range(MAX_PAGES):
            page_listings = get_airbnb_listings(driver)
            for item in page_listings:
                link = item.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_listings.append(item)
            if page_num < MAX_PAGES - 1 and not go_to_next_page(driver):
                break
            time.sleep(1)
        _set_listings(all_listings)
        return jsonify({"ok": True, "count": len(all_listings), "message": f"{len(all_listings)}개 숙소를 수집했습니다."})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/save-excel", methods=["POST"])
def api_save_excel():
    """수집된 목록을 엑셀 파일로 저장 후 다운로드."""
    listings = _get_listings()
    if not listings:
        return jsonify({"ok": False, "message": "저장할 데이터가 없습니다. 먼저 '크롤링 시작'을 실행해 주세요."}), 400
    try:
        filepath = save_listings_to_excel(listings)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


if __name__ == "__main__":
    port = 5000
    print(f"\n>>> 서버 시작: 브라우저에서 아래 주소로 접속하세요.")
    print(f">>> http://127.0.0.1:{port}")
    print(f">>> 또는 http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=False)
