# GitHub Actions 部署指南

## 📌 方案概述

```
GitHub 仓库
    ↓ 每天北京时间 08:00 自动触发（或手动触发）
GitHub Actions 运行 fetch_news.py
    ↓ 抓取 RSS / arXiv / GitHub Trending → 生成 data.js
自动 commit + push 回仓库
    ↓
你的网站数据自动更新 ✅
```

## 🚀 快速部署（3 步完成）

### 第一步：创建 GitHub 仓库

1. 打开 [github.com/new](https://github.com/new)
2. 仓库名：`ai-news-hub`（或你喜欢的名字）
3. **不要勾选** "Add a README file"
4. 选择 **Private** 或 **Public**
5. 点击 **Create repository**

### 第二步：推送代码到 GitHub

在项目目录打开终端，执行：

```bash
cd C:\Users\Administrator\WorkBuddy\2026-05-15-task-2

git init
git add .
git commit -m "🎉 初始化 AI 全球资讯网站"

git remote add origin https://github.com/你的用户名/ai-news-hub.git
git branch -M main
git push -u origin main
```

### 第三步：启用 GitHub Actions（自动生效！）

> **无需任何额外操作！** 只要代码推送到 GitHub，
> `.github/workflows/fetch-news.yml` 文件会自动被识别。

1. 打开你的仓库页面
2. 点击 **Actions** 标签页
3. 左侧应该能看到 `AI News Fetch & Deploy` 工作流
4. 点击它，然后点 **Run workflow** 可立即测试运行

---

## ⏰ 定时任务说明

| 项目 | 设置 |
|------|------|
| **触发时间** | 每天 UTC 00:00 = 北京时间 **08:00** |
| **时区说明** | GitHub 使用 UTC 时区 |
| **手动触发** | 在 Actions 页面点击 **Run workflow** 随时可跑 |

### 修改定时时间

编辑 `.github/workflows/fetch-news.yml` 第 12 行：

```yaml
schedule:
  # 格式: 分 时 日 月 星期(0=周日)
  # UTC时间，北京时间 = UTC + 8小时

  # 北京 08:00 → UTC 00:00
  - cron: '0 0 * * *'

  # 北京 12:00 → UTC 04:00
  # - cron: '0 4 * * *'

  # 北京 20:00 → UTC 12:00
  # - cron: '0 12 * * *'

  # 每6小时一次
  # - cron: '0 */6 * * *'
```

---

## 📂 文件结构说明

```
你的项目/
├── .github/
│   └── workflows/
│       └── fetch-news.yml      ← GitHub Actions 配置（新建）
├── index.html                   ← 网站主页
├── fetch_news.py                ← 数据抓取脚本
├── requirements.txt             ← Python 依赖（新建）
├── css/
│   ├── style.css
│   └── responsive.css
├── js/
│   ├── data.js                  ← 自动生成的数据文件
│   ├── renderer.js              ← 渲染引擎
│   └── main.js                  ← 交互逻辑
├── install_task.ps1             ← Windows 本地定时任务（备选）
├── uninstall_task.ps1           ← 卸载脚本（备选）
└── logs/                        ← 日志目录
```

---

## 🔧 工作流程详解

### Actions 执行步骤

```
Step 1: 检出代码 (Checkout)
    ↓ 从 GitHub 拉取最新代码到 Runner 环境

Step 2: 安装 Python 3.12
    ↓ GitHub 自带 Ubuntu 环境，预装 Python

Step 3: 安装 Python 依赖
    ↓ pip install deep-translator jieba

Step 4: 运行抓取脚本
    ↓ python fetch_news.py
    ↓ 输出: js/data.js（更新后的数据）

Step 5: 检查输出文件
    ↓ 确认 data.js 已正确生成

Step 6: Git 提交变更
    ↓ git add js/data.js
    ↓ git commit -m "🤖 [auto] 更新AI资讯数据"

Step 7: 推送到主分支
    ↓ git push
    ↓ 数据更新完成 ✅
```

### 关键技术点

| 问题 | 解决方案 |
|------|----------|
| 中文编码问题 | `PYTHONUTF8=1` 环境变量 |
| SSL 证书验证 | 脚本中已禁用（`ssl.CERT_NONE`） |
| 依赖管理 | `requirements.txt` 统一管理 |
| 无变更时不提交 | `git diff --cached --quiet` 检查 |
| 超时保护 | `timeout-minutes: 15` |

---

## 📊 监控与管理

### 查看 Actions 运行记录

1. 仓库首页 → **Actions** 标签
2. 点击 **AI News Fetch & Deploy**
3. 可以看到每次运行的详细日志：
   - ✅ 绿色 = 成功
   - ❌ 红色 = 失败（可点击查看错误详情）
   - 🟡 黄色 = 正在运行

### 常见问题排查

#### ❌ 抓取失败（RSS/API 无响应）

**原因**：GitHub Actions 服务器在美国，访问某些国内 RSS 可能慢或超时

**解决**：脚本已设置 15-20 秒超时，个别源失败不影响整体运行。可在日志中看到 `[WARN]` 提示。

#### ❌ 翻译模块失败

**原因**：`deep_translator` 调用 Google Translate，可能被限流

**影响**：翻译失败的文章保留英文原文，不影响网站功能。

#### ❌ data.js 没有变化

**原因**：当天数据与上次相同，或者所有数据源都失败了

**正常现象**：如果 `git diff --cached --quiet` 检测无变化，会跳过提交，避免空提交污染历史。

---

## 🌐 进阶：使用 GitHub Pages 托管网站

如果你想连**网站也一起托管到云端**（零成本、全球 CDN），可以开启 GitHub Pages：

### 方法 A：简单方式（推荐）

1. 仓库页面 → **Settings** → **Pages**
2. **Source** 选择 **Deploy from a branch**
3. Branch 选 **main**，文件夹选 **/(root)**
4. 点击 **Save**

几分钟后，你的网站就可以通过：
```
https://你的用户名.github.io/ai-news-hub/
```
访问了！

### 方法 B：通过 Actions 自动部署

取消 `.github/workflows/fetch-news.yml` 文件底部 `deploy-pages` 任务的注释即可实现：
- 每次数据更新后，自动重新部署网站
- 使用 GitHub 官方 CDN 加速全球访问

### 绑定自定义域名（可选）

在 Pages 设置中添加自定义域名：
1. Settings → Pages → Custom domain
2. 输入如 `ai-news.yourdomain.com`
3. 在域名 DNS 添加 CNAME 记录指向 `<user>.github.io`

---

## 💡 对比：GitHub Actions vs Windows 定时任务

| 特性 | GitHub Actions | Windows 定时任务 |
|------|----------------|------------------|
| **成本** | 免费（公开仓库无限额度） | 免费（本地运行） |
| **服务器** | 云端 Ubuntu | 你的电脑 |
| **开机要求** | 不需要 | 电脑必须开着 |
| **网络环境** | 海外节点（访问 GitHub/arXiv 快） | 本地网络 |
| **维护性** | 高（配置即代码） | 低（依赖本机环境） |
| **可追溯** | 完整的运行日志和状态 | 需要自己看日志文件 |
| **适合场景** | **长期稳定运行** | 开发调试阶段 |

---

## 🔄 回退方案

如果 GitHub Actions 出问题，随时可以切回本地定时任务：

```powershell
# 本地安装定时任务
.\install_task.ps1

# 或者手动运行
$env:PYTHONUTF8=1; python.exe fetch_news.py
```

---

## 📝 下一步建议

- [ ] 创建 GitHub 仓库并推送代码
- [ ] 手动触发一次 Action 测试效果
- [ ] （可选）开启 GitHub Pages 托管网站
- [ ] （可选）绑定自定义域名
