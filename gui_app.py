"""
에어비앤비 크롤링 데스크톱 GUI (tkinter)
- 홈페이지 접속 / 크롤링 시작 / 엑셀 저장 버튼
- 실행 파일(.exe)로 배포 가능
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# exe로 실행 시 작업 폴더를 exe 위치로
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_APP_DIR)

# main 모듈은 GUI 초기화 후 지연 로드 (import 오류 메시지 표시용)
_main = None


def _get_main():
    global _main
    if _main is None:
        import main as m
        _main = m
    return _main


class CrawlerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("에어비앤비 크롤링")
        self.root.geometry("420x380")
        self.root.resizable(True, True)
        self.root.minsize(380, 320)

        self.driver = None
        self.listings = []
        self._lock = threading.Lock()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}
        f = ttk.Frame(self.root, padding=16)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="에어비앤비 크롤링", font=("", 14, "bold")).pack(pady=(0, 12))

        # 최대 크롤링 페이지 수 (1~20)
        row_pages = ttk.Frame(f)
        row_pages.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(row_pages, text="최대 크롤링 페이지 수:").pack(side=tk.LEFT, padx=(0, 8))
        self.max_pages_var = tk.StringVar(value="3")
        self.spin_pages = tk.Spinbox(
            row_pages,
            from_=1,
            to=20,
            width=4,
            textvariable=self.max_pages_var,
            font=("", 10),
        )
        self.spin_pages.pack(side=tk.LEFT)
        ttk.Label(row_pages, text="페이지").pack(side=tk.LEFT, padx=(4, 0))

        self.btn_open = ttk.Button(f, text="홈페이지 접속", command=self._on_open_homepage)
        self.btn_open.pack(fill=tk.X, **pad)

        self.btn_crawl = ttk.Button(f, text="크롤링 시작", command=self._on_start_crawl)
        self.btn_crawl.pack(fill=tk.X, **pad)

        self.btn_excel = ttk.Button(f, text="엑셀 저장", command=self._on_save_excel)
        self.btn_excel.pack(fill=tk.X, **pad)

        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(f, text="상태").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(f, height=8, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _log(self, msg: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _set_buttons_state(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_open.config(state=state)
        self.btn_crawl.config(state=state)
        self.btn_excel.config(state=state)

    def _on_open_homepage(self):
        self._set_buttons_state(False)
        self._log("홈페이지 접속 중...")

        def run():
            try:
                main = _get_main()
                with self._lock:
                    if self.driver:
                        try:
                            self.driver.quit()
                        except Exception:
                            pass
                        self.driver = None
                time.sleep(0.5)
                driver = main.create_driver(headless=False)
                with self._lock:
                    self.driver = driver
                time.sleep(1)
                main.open_airbnb_page(driver)
                self.root.after(0, lambda: self._log("에어비앤비 홈페이지를 열었습니다. 검색/필터 후 '크롤링 시작'을 누르세요."))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"오류: {e}"))
                self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
            finally:
                self.root.after(0, lambda: self._set_buttons_state(True))

        threading.Thread(target=run, daemon=True).start()

    def _on_start_crawl(self):
        with self._lock:
            driver = self.driver
        if not driver:
            messagebox.showwarning("안내", "먼저 '홈페이지 접속'을 눌러 주세요.")
            return

        try:
            max_pages = int(self.max_pages_var.get().strip())
            if max_pages < 1 or max_pages > 20:
                raise ValueError("1~20 사이로 입력하세요.")
        except ValueError as e:
            messagebox.showwarning("입력 오류", "최대 크롤링 페이지 수는 1~20 사이의 숫자로 입력하세요.")
            return

        self._set_buttons_state(False)
        self._log(f"크롤링 시작 (최대 {max_pages}페이지)...")

        def run():
            try:
                main = _get_main()
                main.accept_cookie_if_any(driver)
                time.sleep(0.3)
                all_listings = []
                seen = set()
                for page_num in range(max_pages):
                    self.root.after(0, lambda p=page_num: self._log(f"  {p + 1}페이지 수집 중..."))
                    page_listings = main.get_airbnb_listings(driver)
                    for item in page_listings:
                        link = item.get("link", "")
                        if link and link not in seen:
                            seen.add(link)
                            all_listings.append(item)
                    if page_num < max_pages - 1 and not main.go_to_next_page(driver):
                        break
                    time.sleep(1)
                with self._lock:
                    self.listings = all_listings
                self.root.after(0, lambda: self._log(f"완료: {len(all_listings)}개 숙소 수집했습니다."))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"오류: {e}"))
                self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
            finally:
                self.root.after(0, lambda: self._set_buttons_state(True))

        threading.Thread(target=run, daemon=True).start()

    def _on_save_excel(self):
        with self._lock:
            listings = list(self.listings)
        if not listings:
            messagebox.showwarning("안내", "저장할 데이터가 없습니다. 먼저 '크롤링 시작'을 실행해 주세요.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            initialdir=_APP_DIR,
            initialfile=f"airbnb_listings_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not path:
            return
        try:
            main = _get_main()
            main.save_listings_to_excel(listings, filepath=path)
            self._log(f"엑셀 저장: {path}")
            messagebox.showinfo("저장 완료", f"저장했습니다.\n{path}")
        except Exception as e:
            self._log(f"저장 오류: {e}")
            messagebox.showerror("오류", str(e))

    def _on_close(self):
        with self._lock:
            driver = self.driver
            self.driver = None
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = CrawlerGUI()
    app.run()


if __name__ == "__main__":
    main()
