# ============================================================
# Windows 任务计划程序 - AI资讯自动抓取 安装脚本
# 功能：每天定时运行 fetch_news.py 更新数据
# 使用方法：右键 PowerShell → "以管理员身份运行" → 执行本脚本
# ============================================================

$TaskName = "AI资讯自动抓取"
$ScriptDir = $PSScriptRoot
$PythonPath = "python.exe"
$ScriptPath = Join-Path $ScriptDir "fetch_news.py"
$LogFile   = Join-Path $ScriptDir "logs\scheduler.log"

# 确保 logs 目录存在
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AI 资讯自动抓取 - Windows 定时任务安装"   -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "任务名称: $TaskName"
Write-Host "脚本路径: $ScriptPath"
Write-Host "工作目录: $ScriptDir"
Write-Host ""

# 检查脚本文件是否存在
if (-not (Test-Path $ScriptPath)) {
    Write-Host "[错误] 找不到脚本文件: $ScriptPath" -ForegroundColor Red
    Write-Host "请确保在正确目录下运行此脚本。" -ForegroundColor Yellow
    pause
    exit 1
}

# 检查 Python 是否可用
try {
    $PythonVersion = & $PythonPath --version 2>&1
    Write-Host "[OK] Python 已找到: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 找不到 Python，请确保 python.exe 在 PATH 中。" -ForegroundColor Red
    Write-Host "或者修改本脚本第 7 行的 `$PythonPath 为完整路径。" -ForegroundColor Yellow
    pause
    exit 1
}

# 如果已存在同名任务，先删除
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "[警告] 已存在同名任务 '$TaskName'，将先删除再重建..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# --- 构建任务动作 ---
# 使用 cmd /c 来确保环境变量正确设置
$ActionScript = @"
cmd /c "set PYTHONUTF8=1 && cd /d `"$ScriptDir`" && `$PythonPath fetch_news.py >> `"$LogFile`" 2>&1"
"@

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c set PYTHONUTF8=1 && cd /d `"$ScriptDir`" && $PythonPath fetch_news.py >> `"$LogFile`" 2>&1"

# --- 构建任务触发器（每天早上 8:00 运行）---
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00"

# --- 任务设置 ---
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# --- 任务主体（不管用户是否登录都运行）---
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# --- 注册任务 ---
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "每天自动抓取 AI 资讯（量子位RSS、arXiv论文、GitHub Trending），更新 js/data.js 数据文件。"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  [OK] 定时任务安装成功！"                  -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "任务详情:"                                 -ForegroundColor Yellow
Write-Host "  名称: $TaskName"
Write-Host "  触发器: 每天 08:00"
Write-Host "  执行: $PythonPath fetch_news.py"
Write-Host "  日志: $LogFile"
Write-Host ""
Write-Host "管理命令:"                                 -ForegroundColor Cyan
Write-Host "  查看任务:   taskschd.msc（任务计划程序）"
Write-Host "  手动运行:   Right-Click 任务 → 运行"
Write-Host "  删除任务:   Unregister-ScheduledTask -TaskName `"$TaskName`""
Write-Host "  修改时间:   在任务计划程序中右键任务 → 属性 → 触发器"
Write-Host ""
Write-Host "是否立即运行一次测试？(Y/N) " -NoNewline -ForegroundColor Yellow
$TestRun = Read-Host
if ($TestRun -eq "Y" -or $TestRun -eq "y") {
    Write-Host "正在运行任务..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "任务状态: $($TaskInfo.LastTaskResult)" -ForegroundColor Green
    Write-Host "查看日志: notepad.exe `"$LogFile`"" -ForegroundColor Cyan
}

pause
