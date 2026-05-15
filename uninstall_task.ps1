# ============================================================
# Windows 任务计划程序 - 卸载 AI资讯自动抓取 任务
# ============================================================

$TaskName = "AI资讯自动抓取"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AI 资讯自动抓取 - 卸载脚本"              -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $ExistingTask) {
    Write-Host "[提示] 未找到任务 '$TaskName'，无需卸载。" -ForegroundColor Yellow
    pause
    exit 0
}

Write-Host "找到任务: $TaskName" -ForegroundColor Yellow
Write-Host "是否确认删除？(Y/N) " -NoNewline -ForegroundColor Red
$Confirm = Read-Host
if ($Confirm -ne "Y" -and $Confirm -ne "y") {
    Write-Host "已取消。" -ForegroundColor Yellow
    pause
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host ""
Write-Host "[OK] 任务 '$TaskName' 已成功删除！" -ForegroundColor Green
Write-Host ""
pause
