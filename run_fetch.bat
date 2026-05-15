@echo off
chcp 65001 > nul
echo [AI全球资讯] 开始每日内容抓取...
cd /d "%~dp0"

"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" fetch_news.py >> logs\fetch_log_%date:~0,4%%date:~5,2%%date:~8,2%.txt 2>&1

if %errorlevel% equ 0 (
    echo [AI全球资讯] 完成！已更新 js\data.js
) else (
    echo [AI全球资讯] 失败！错误码：%errorlevel%
)
