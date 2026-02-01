@echo off
chcp 65001 >nul
echo 에어비앤비 크롤링 - 배포용 exe 빌드
echo.

cd /d "%~dp0"

REM 실행 중인 exe가 있으면 빌드 실패할 수 있음
if exist "dist\AirbnbCrawler.exe" (
    echo [안내] 기존 dist\AirbnbCrawler.exe 가 있습니다. 빌드 중 덮어쓰기 오류가 나면 해당 exe를 종료한 뒤 다시 실행하세요.
    echo.
)

python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller가 없습니다. 설치 중...
    python -m pip install pyinstaller
)

echo.
echo 빌드 시작 (build_exe.spec)...
python -m PyInstaller --noconfirm build_exe.spec

if exist "dist\AirbnbCrawler.exe" (
    echo.
    echo ===== 빌드 완료 =====
    echo 배포용 실행 파일: dist\AirbnbCrawler.exe
    echo 이 파일만 복사해 다른 PC에서 실행할 수 있습니다.
    echo 자세한 내용은 배포안내.txt 를 참고하세요.
) else (
    echo.
    echo 빌드 실패. 액세스 거부 시: exe 종료 후 재시도, 또는 관리자 권한으로 실행.
    echo 배포안내.txt 를 참고하세요.
)

echo.
pause
