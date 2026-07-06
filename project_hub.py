from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import locale


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "dashboard_config.json"
HOST = os.environ.get("PROJECT_HUB_HOST", "127.0.0.1")
PORT = int(os.environ.get("PROJECT_HUB_PORT", "5066"))
PROJECT_ROOT = Path(r"D:\py project")


def p(name: str) -> str:
    return str(PROJECT_ROOT / name)


DEFAULT_PROJECTS: list[dict[str, Any]] = [
    {
        "id": "zge",
        "name": "Z哥炒股智能系统",
        "path": p("zge"),
        "category": "Web / A股决策",
        "purpose": "基于 Z 哥体系的择时、选股、策略回测、持仓管理和每日复盘 Web 应用。",
        "usage": "先启动后端，再启动前端；浏览前端页面进行看盘、筛选和复盘。",
        "startup_steps": ["安装 backend/requirements.txt", "在 frontend 安装 npm 依赖", "启动 FastAPI 后端", "启动 Vite 前端"],
        "links": [{"label": "前端", "url": "http://127.0.0.1:5173"}, {"label": "API 文档", "url": "http://127.0.0.1:8000/docs"}],
        "commands": [
            {"id": "backend", "label": "后端 8000", "cwd": p(r"zge\backend"), "command": "python main.py", "url": "http://127.0.0.1:8000/docs"},
            {"id": "frontend", "label": "前端 5173", "cwd": p(r"zge\frontend"), "command": "npm run dev -- --host 127.0.0.1", "url": "http://127.0.0.1:5173"},
        ],
        "config_vars": [],
    },
    {
        "id": "czsc",
        "name": "czsc 缠论分析库",
        "path": p("czsc"),
        "category": "Library / 量化分析",
        "purpose": "缠中说禅技术分析工具库，包含 Python 包和 Rust 扩展。",
        "usage": "日常主要作为库调用；面板提供版本检查和测试入口。",
        "startup_steps": ["需要 Python 3.10+", "开发构建使用 maturin / cargo", "按需运行测试或版本检查"],
        "commands": [
            {"id": "version", "label": "版本检查", "cwd": p("czsc"), "command": "python -c \"import czsc; print(getattr(czsc, '__version__', 'czsc imported'))\""},
            {"id": "tests", "label": "运行测试", "cwd": p("czsc"), "command": "python -m pytest tests -q"},
        ],
        "config_vars": [],
    },
    {
        "id": "wyckoff_trading",
        "name": "AI × Wyckoff 量化分析系统",
        "path": p("wyckoff-trading"),
        "category": "Web / 威科夫分析",
        "purpose": "基于威科夫法则的个股分析、五层筛选评分、共振判断、回测和市场扫描。",
        "usage": "先启动 FastAPI 后端，再启动前端，在浏览器中查看分析面板。",
        "startup_steps": ["安装 backend/requirements.txt", "在 frontend 安装 npm 依赖", "启动后端", "启动前端"],
        "links": [{"label": "前端", "url": "http://127.0.0.1:5174"}, {"label": "API 文档", "url": "http://127.0.0.1:8001/docs"}],
        "commands": [
            {"id": "backend", "label": "后端 8001", "cwd": p("wyckoff-trading\\backend"), "command": "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload", "url": "http://127.0.0.1:8001/docs"},
            {"id": "frontend", "label": "前端 5174", "cwd": p("wyckoff-trading\\frontend"), "command": "npm run dev -- --host 127.0.0.1 --port 5174", "url": "http://127.0.0.1:5174"},
        ],
        "config_vars": [],
    },
    {
        "id": "duanxian_t",
        "name": "短线 T 策略面板",
        "path": p("duanxianT"),
        "category": "Web / T策略",
        "purpose": "网格、懒人 T、智能 T 回测与持仓监控工具。",
        "usage": "启动 Flask 面板后，在浏览器中维护组合、查看信号和回测结果。",
        "startup_steps": ["安装 Flask 等 Python 依赖", "可用 T_UI_PORT 指定端口", "运行 web_app.py"],
        "links": [{"label": "Web", "url": "http://127.0.0.1:5050"}],
        "commands": [{"id": "web", "label": "Web 5050", "cwd": p("duanxianT"), "command": "python web_app.py", "url": "http://127.0.0.1:5050"}],
        "config_vars": [{"name": "T_UI_PORT", "label": "端口", "placeholder": "5050"}],
    },
    {
        "id": "shortais",
        "name": "短线助手",
        "path": p("shortais"),
        "category": "Web / 强势股筛选",
        "purpose": "成交额、热度、动量和板块强度综合评分，辅助短线强势股筛选。",
        "usage": "启动 Flask 页面后点击重新运行，按数据获取、筛选评分、结果展示的流程执行。",
        "startup_steps": ["安装 requirements.txt", "运行 app.py", "浏览 http://127.0.0.1:5678"],
        "links": [{"label": "Web", "url": "http://127.0.0.1:5678"}],
        "commands": [{"id": "web", "label": "Web 5678", "cwd": p("shortais"), "command": "python app.py", "url": "http://127.0.0.1:5678"}],
        "config_vars": [],
    },
    {
        "id": "stock_tracker",
        "name": "股票跟踪助手",
        "path": p("stock_tracker"),
        "category": "Streamlit / 跟踪复盘",
        "purpose": "持仓、自选股、复盘模板和股票分析报告管理。",
        "usage": "启动 Streamlit 后在浏览器维护跟踪列表和复盘内容。",
        "startup_steps": ["安装 requirements.txt", "初始化数据库", "运行 Streamlit 应用"],
        "links": [{"label": "Streamlit", "url": "http://127.0.0.1:8501"}],
        "commands": [{"id": "streamlit", "label": "Streamlit 8501", "cwd": p("stock_tracker"), "command": "python -m streamlit run stock_tracker_app.py --server.port 8501 --server.address localhost", "url": "http://127.0.0.1:8501"}],
        "config_vars": [],
    },
    {
        "id": "valuecell",
        "name": "ValueCell",
        "path": p("valuecell"),
        "category": "Full-stack / 研究工具",
        "purpose": "带前端和 Python 后端的价值研究工作台。",
        "usage": "可用项目自带 start.ps1 一键拉起；也可分别启动前后端。",
        "startup_steps": ["确认 bun 和 uv 可用", "运行 start.ps1", "或分别进入 frontend/python 启动"],
        "commands": [{"id": "launcher", "label": "一键启动", "cwd": p("valuecell"), "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .\\start.ps1"}],
        "config_vars": [],
    },
    {
        "id": "newsnow",
        "name": "NewsNow",
        "path": p("newsnow"),
        "category": "Web / 新闻聚合",
        "purpose": "新闻源聚合与浏览项目，适合每日查看市场资讯。",
        "usage": "启动 Vite 开发服务，在浏览器查看资讯列表。",
        "startup_steps": ["安装 npm 依赖", "确认 example.env.server 已按需复制配置", "运行 npm run dev"],
        "links": [{"label": "Web", "url": "http://127.0.0.1:5175"}],
        "commands": [{"id": "dev", "label": "开发服务 5175", "cwd": p("newsnow"), "command": "npm run dev -- --host 127.0.0.1 --port 5175", "url": "http://127.0.0.1:5175"}],
        "config_vars": [],
    },
    {
        "id": "daily_stock_analysis",
        "name": "A股智能分析系统",
        "path": p("daily_stock_analysis"),
        "category": "CLI / 每日分析",
        "purpose": "基于行情、新闻搜索和 AI 模型生成自选股分析与推送。",
        "usage": "配置模型 Key、股票池和推送渠道后运行 main.py；可 dry-run 或只做大盘复盘。",
        "startup_steps": ["安装 requirements.txt", "配置至少一个 AI 模型 Key", "配置 STOCK_LIST", "运行 main.py"],
        "commands": [
            {"id": "dry_run", "label": "Dry run", "cwd": p("daily_stock_analysis"), "command": "python main.py --dry-run --no-notify"},
            {"id": "full", "label": "完整分析", "cwd": p("daily_stock_analysis"), "command": "python main.py"},
            {"id": "market", "label": "大盘复盘", "cwd": p("daily_stock_analysis"), "command": "python main.py --market-review"},
        ],
        "config_vars": [
            {"name": "GEMINI_API_KEY", "label": "Gemini API Key", "secret": True},
            {"name": "OPENAI_API_KEY", "label": "OpenAI 兼容 Key", "secret": True},
            {"name": "OPENAI_BASE_URL", "label": "OpenAI Base URL", "placeholder": "https://api.deepseek.com/v1"},
            {"name": "OPENAI_MODEL", "label": "模型名称", "placeholder": "deepseek-chat"},
            {"name": "STOCK_LIST", "label": "股票池", "placeholder": "600519,300750,002594"},
            {"name": "TAVILY_API_KEYS", "label": "Tavily Key", "secret": True},
            {"name": "BOCHA_API_KEYS", "label": "博查 Key", "secret": True},
            {"name": "SERPAPI_API_KEYS", "label": "SerpAPI Key", "secret": True},
            {"name": "TUSHARE_TOKEN", "label": "Tushare Token", "secret": True},
            {"name": "WECHAT_WEBHOOK_URL", "label": "企业微信 Webhook", "secret": True},
            {"name": "FEISHU_WEBHOOK_URL", "label": "飞书 Webhook", "secret": True},
        ],
    },
    {
        "id": "a_share_platform",
        "name": "股票平台期扫描工具",
        "path": p("a-share-platform-stocks-selection"),
        "category": "Web / 平台期扫描",
        "purpose": "A 股平台期形态扫描与前端展示工具。",
        "usage": "启动 Vite 开发服务，在页面中查看扫描工具。",
        "startup_steps": ["安装 npm 依赖", "运行 npm run dev", "浏览 5176 端口"],
        "links": [{"label": "Web", "url": "http://127.0.0.1:5176"}],
        "commands": [{"id": "dev", "label": "开发服务 5176", "cwd": p("a-share-platform-stocks-selection"), "command": "npm run dev -- --host 127.0.0.1 --port 5176", "url": "http://127.0.0.1:5176"}],
        "config_vars": [],
    },
    {
        "id": "finrobot",
        "name": "FinRobot",
        "path": p("FinRobot"),
        "category": "AI Agent / 金融分析",
        "purpose": "金融 AI Agent 平台，包含研报、年报、交易策略等多类智能体示例。",
        "usage": "通常先配置 OAI_CONFIG_LIST 或相关 API Key，再运行示例脚本或 Notebook。",
        "startup_steps": ["创建 Python 3.10 环境", "安装 requirements.txt", "配置模型和金融数据源 Key", "运行 demo 或教程"],
        "commands": [
            {"id": "demo", "label": "Agent demo", "cwd": p("FinRobot"), "command": "python agent_builder_demo.py"},
            {"id": "test", "label": "模块测试", "cwd": p("FinRobot"), "command": "python test_module.py"},
        ],
        "config_vars": [
            {"name": "OPENAI_API_KEY", "label": "OpenAI API Key", "secret": True},
            {"name": "FINNHUB_API_KEY", "label": "Finnhub Key", "secret": True},
            {"name": "FMP_API_KEY", "label": "FMP Key", "secret": True},
            {"name": "SEC_API_API_KEY", "label": "SEC API Key", "secret": True},
        ],
    },
    {
        "id": "nine_dimension_invest",
        "name": "九维投资决策系统",
        "path": p("nine_dimension_invest"),
        "category": "Streamlit / 九维评分",
        "purpose": "基于九维评分、市场情绪和自选股配置的投资仪表盘。",
        "usage": "配置 Tushare Token 和股票池后启动 Streamlit dashboard。",
        "startup_steps": ["安装 streamlit/pandas/tushare 等依赖", "配置 TUSHARE_TOKEN", "运行 dashboard.py"],
        "links": [{"label": "Streamlit", "url": "http://127.0.0.1:8502"}],
        "commands": [{"id": "streamlit", "label": "Streamlit 8502", "cwd": p("nine_dimension_invest"), "command": "python -m streamlit run dashboard.py --server.port 8502 --server.address localhost", "url": "http://127.0.0.1:8502"}],
        "config_vars": [
            {"name": "TUSHARE_TOKEN", "label": "Tushare Token", "secret": True},
            {"name": "DINGTALK_WEBHOOK", "label": "钉钉 Webhook", "secret": True},
        ],
    },
    {
        "id": "czsc_skills",
        "name": "czsc_skills",
        "path": p("czsc_skills"),
        "category": "Skill / 缠论",
        "purpose": "围绕 czsc 库构建的缠论 Claude Skills 仓库。",
        "usage": "作为技能仓库引用或打包；日常可查看 README 和技能脚本。",
        "startup_steps": ["查看 skills/czsc-thinking", "按目标 Agent 的插件/技能方式安装", "需要时运行脚本获取行情和结构分析"],
        "commands": [{"id": "list", "label": "列出 Skills", "cwd": p("czsc_skills"), "command": "powershell -NoProfile -Command \"Get-ChildItem -Recurse -Filter SKILL.md | Select-Object -ExpandProperty FullName\""}],
        "config_vars": [{"name": "TUSHARE_TOKEN", "label": "Tushare Token", "secret": True}],
    },
    {
        "id": "zettaranc_skill",
        "name": "zettaranc-skill",
        "path": p("zettaranc-skill"),
        "category": "Skill / 投资认知",
        "purpose": "Zettaranc（z哥）投资认知操作系统技能。",
        "usage": "作为 Codex/Agent Skill 使用；主要价值在 SKILL.md 和 references。",
        "startup_steps": ["阅读 SKILL.md", "按目标 Agent 的技能目录安装", "在对话中切换到 z哥视角"],
        "commands": [{"id": "show", "label": "查看入口", "cwd": p("zettaranc-skill"), "command": "python -c \"from pathlib import Path; print(Path('SKILL.md').read_text(encoding='utf-8')[:3200])\""}],
        "config_vars": [],
    },
    {
        "id": "uzi_skill",
        "name": "UZI-Skill",
        "path": p("UZI-Skill"),
        "category": "Skill / 深度个股分析",
        "purpose": "A/H/美股个股深度分析技能，包含多维数据、机构方法和报告生成。",
        "usage": "安装依赖后可直接运行 run.py 股票名，也可作为 Agent 插件/Skill 使用。",
        "startup_steps": ["安装 requirements.txt", "可选配置 MX_APIKEY", "运行 python run.py 股票名"],
        "commands": [
            {"id": "quick", "label": "示例分析", "cwd": p("UZI-Skill"), "command": "python run.py 贵州茅台"},
            {"id": "tests", "label": "运行测试", "cwd": p("UZI-Skill"), "command": "python -m pytest -q"},
        ],
        "config_vars": [
            {"name": "MX_APIKEY", "label": "东财妙想 API Key", "secret": True},
            {"name": "STOCK_NO_CACHE", "label": "禁用缓存", "placeholder": "1"},
            {"name": "UZI_NO_AUTO_OPEN", "label": "禁止自动打开浏览器", "placeholder": "1"},
        ],
    },
]

README_CANDIDATES = (
    "README.md",
    "README.zh-CN.md",
    "README.zh.md",
    "README.txt",
    "使用说明.md",
    "SKILL.md",
    "AGENTS.md",
)


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Py Project Hub</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef0ed;
      --panel: #ffffff;
      --panel-2: #f7f7f4;
      --text: #1d2420;
      --muted: #65706a;
      --line: #d9ded8;
      --accent: #116a56;
      --accent-2: #b16b2b;
      --danger: #b33a32;
      --running: #17895d;
      --idle: #848b82;
      --term: #101511;
      --term-text: #d8f2dd;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }
    header {
      position: sticky;
      top: 0;
      z-index: 5;
      border-bottom: 1px solid var(--line);
      background: rgba(238, 240, 237, .96);
      backdrop-filter: blur(10px);
    }
    .topbar {
      max-width: 1480px;
      margin: 0 auto;
      padding: 18px 22px;
      display: grid;
      grid-template-columns: 1fr minmax(260px, 420px);
      gap: 16px;
      align-items: center;
    }
    h1 { margin: 0; font-size: 24px; line-height: 1.25; }
    .subtitle { color: var(--muted); margin-top: 5px; font-size: 13px; }
    .search {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--text);
      padding: 9px 10px;
      font: inherit;
      min-width: 0;
    }
    textarea { min-height: 58px; resize: vertical; line-height: 1.45; }
    button, .link-button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 8px;
      min-height: 34px;
      padding: 7px 11px;
      font: inherit;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
    }
    button:hover, .link-button:hover { border-color: #aeb9af; background: #fbfbf8; }
    button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
    button.warning { background: #fff7ed; border-color: #e0b17e; color: #8a4e19; }
    button.danger { background: #fff4f2; border-color: #e3a29c; color: var(--danger); }
    button:disabled { opacity: .55; cursor: not-allowed; }
    main {
      max-width: 1480px;
      margin: 0 auto;
      padding: 20px 22px 40px;
    }
    .summary {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
      color: var(--muted);
      font-size: 13px;
    }
    .pill {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.62);
      padding: 6px 10px;
      border-radius: 999px;
    }
    .external-section {
      margin-bottom: 18px;
      display: grid;
      gap: 10px;
    }
    .section-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
    }
    .section-head h2 {
      margin: 0;
      font-size: 17px;
      line-height: 1.3;
    }
    .site-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }
    .site-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.78);
      border-radius: 8px;
      padding: 13px;
      display: grid;
      gap: 9px;
      box-shadow: 0 8px 22px rgba(39, 49, 43, .045);
    }
    .site-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
    }
    .site-name {
      font-size: 16px;
      line-height: 1.25;
      font-weight: 800;
    }
    .site-url {
      color: var(--muted);
      font: 12px Consolas, "Courier New", monospace;
      overflow-wrap: anywhere;
    }
    .site-desc {
      color: #344039;
      font-size: 13px;
      line-height: 1.52;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(390px, 1fr));
      gap: 16px;
      align-items: start;
    }
    .project {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 8px 22px rgba(39, 49, 43, .06);
    }
    .project-head {
      padding: 15px;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 9px;
    }
    .title-row {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .project h2 {
      margin: 0;
      font-size: 18px;
      line-height: 1.28;
      overflow-wrap: anywhere;
    }
    .category { color: var(--accent-2); font-size: 12px; font-weight: 700; }
    .status {
      font-size: 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      color: var(--idle);
      background: var(--panel-2);
      flex: 0 0 auto;
    }
    .status.running { color: var(--running); border-color: #9fd8bd; background: #effaf3; }
    .body { padding: 14px 15px 15px; display: grid; gap: 13px; }
    .desc { color: #344039; line-height: 1.55; font-size: 14px; }
    .path {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      color: var(--muted);
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      overflow-wrap: anywhere;
    }
    .steps { margin: 0; padding-left: 18px; color: var(--muted); font-size: 13px; line-height: 1.5; }
    .section-title { font-size: 13px; font-weight: 800; color: #2c3530; margin-bottom: 7px; }
    .commands { display: grid; gap: 10px; }
    .command {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
      padding: 10px;
      display: grid;
      gap: 8px;
    }
    .command-top {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
    }
    .command-label { font-weight: 800; font-size: 13px; }
    .command-actions { display: flex; gap: 7px; flex-wrap: wrap; }
    .cmdline {
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }
    .terminal {
      height: 170px;
      overflow: auto;
      background: var(--term);
      color: var(--term-text);
      border-radius: 8px;
      padding: 10px;
      font: 12px/1.5 Consolas, "Courier New", monospace;
      white-space: pre-wrap;
      border: 1px solid #1f2a22;
    }
    .config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 9px; }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 12px; }
    .save-row, .links { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .muted { color: var(--muted); font-size: 12px; }
    .empty {
      padding: 28px;
      color: var(--muted);
      border: 1px dashed #b8c1b8;
      border-radius: 8px;
      background: rgba(255,255,255,.55);
      text-align: center;
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 20;
      background: rgba(14, 21, 17, .48);
      display: none;
      align-items: stretch;
      justify-content: center;
      padding: 28px;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      width: min(980px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 50px rgba(0,0,0,.24);
      display: grid;
      grid-template-rows: auto 1fr;
      overflow: hidden;
    }
    .modal-head {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    .modal-title { font-size: 15px; font-weight: 800; }
    .readme-path { color: var(--muted); font: 12px Consolas, "Courier New", monospace; margin-top: 3px; overflow-wrap: anywhere; }
    .readme-content {
      margin: 0;
      padding: 16px;
      overflow: auto;
      white-space: pre-wrap;
      font: 13px/1.55 Consolas, "Courier New", monospace;
      background: #fbfbf8;
    }
    @media (max-width: 760px) {
      .topbar { grid-template-columns: 1fr; padding: 15px; }
      main { padding: 15px; }
      .grid { grid-template-columns: 1fr; }
      .command-top { grid-template-columns: 1fr; }
      .terminal { height: 150px; }
      .modal-backdrop { padding: 12px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>Py Project Hub</h1>
        <div class="subtitle">每日项目面板、启动器、配置参数和控制台日志</div>
      </div>
      <div class="search">
        <input id="search" placeholder="搜索项目、用途、路径或分类">
        <button id="refresh">刷新</button>
      </div>
    </div>
  </header>
  <main>
    <div class="summary" id="summary"></div>
    <section class="external-section" aria-labelledby="externalSitesTitle">
      <div class="section-head">
        <h2 id="externalSitesTitle">常看外部网站</h2>
        <span class="muted">投研导航、策略工具和产业链地图</span>
      </div>
      <div class="site-grid" id="externalSites"></div>
    </section>
    <div class="grid" id="projects"></div>
  </main>
  <div class="modal-backdrop" id="readmeModal" role="dialog" aria-modal="true">
    <div class="modal">
      <div class="modal-head">
        <div>
          <div class="modal-title" id="readmeTitle">README</div>
          <div class="readme-path" id="readmePath"></div>
        </div>
        <button id="closeReadme">关闭</button>
      </div>
      <pre class="readme-content" id="readmeContent"></pre>
    </div>
  </div>
  <script>
    const EXTERNAL_SITES = [
      {
        name: "一技之长",
        url: "https://www.zgnb.top/home",
        desc: "常用资源与工具聚合首页，适合放在每日工作流入口，快速跳转到个人常看的内容。"
      },
      {
        name: "大鸡腿策略馆",
        url: "https://www.dajitui.vip/",
        desc: "量化策略与交易工具导航站，适合查看策略资源、市场工具和投研辅助入口。"
      },
      {
        name: "AI产业链地图",
        url: "https://aichainmap.com/",
        desc: "AI 产业链知识地图，用来梳理上游算力、模型、应用、企业与相关投研线索。"
      }
    ];
    const state = { projects: [], filter: "" };

    const $ = (sel) => document.querySelector(sel);
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

    async function api(path, options = {}) {
      const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || res.statusText);
      return data;
    }

    function projectRunning(project) {
      return project.commands.some(c => c.status && c.status.running);
    }

    function renderSummary(projects) {
      const running = projects.filter(projectRunning).length;
      const commands = projects.reduce((n, p) => n + p.commands.length, 0);
      $("#summary").innerHTML = `
        <span class="pill">项目 ${projects.length}</span>
        <span class="pill">启动项 ${commands}</span>
        <span class="pill">运行中 ${running}</span>
        <span class="pill">外部网站 ${EXTERNAL_SITES.length}</span>
        <span class="pill">配置保存在 dashboard_config.json</span>
      `;
    }

    function renderExternalSites() {
      $("#externalSites").innerHTML = EXTERNAL_SITES.map(site => `
        <article class="site-card">
          <div class="site-top">
            <div>
              <div class="site-name">${esc(site.name)}</div>
              <div class="site-url">${esc(site.url.replace(/^https?:\/\//, ""))}</div>
            </div>
            <a class="link-button" href="${esc(site.url)}" target="_blank" rel="noreferrer">打开网站</a>
          </div>
          <div class="site-desc">${esc(site.desc)}</div>
        </article>
      `).join("");
    }

    function commandHtml(project, cmd) {
      const running = cmd.status && cmd.status.running;
      const pid = project.id;
      const cid = cmd.id;
      return `
        <div class="command" data-pid="${esc(pid)}" data-cid="${esc(cid)}">
          <div class="command-top">
            <div>
              <div class="command-label">${esc(cmd.label || cid)} ${running ? `<span class="status running">PID ${esc(cmd.status.pid)}</span>` : `<span class="status">未运行</span>`}</div>
              <div class="muted">${esc(cmd.cwd || project.path)}</div>
            </div>
            <div class="command-actions">
              <button class="primary" data-action="start" ${running ? "disabled" : ""}>启动</button>
              <button class="danger" data-action="stop" ${running ? "" : "disabled"}>停止</button>
              <button data-action="clear">清屏</button>
              ${cmd.url ? `<a class="link-button" href="${esc(cmd.url)}" target="_blank" rel="noreferrer">打开</a>` : ""}
            </div>
          </div>
          <textarea class="cmdline" data-field="command">${esc(cmd.command || "")}</textarea>
          <div class="terminal" id="term-${esc(pid)}-${esc(cid)}">${esc((cmd.logs || []).join(""))}</div>
        </div>
      `;
    }

    function configHtml(project) {
      const vars = project.config_vars || [];
      if (!vars.length) return `<div class="muted">暂无需要配置的参数。</div>`;
      return `
        <div class="config-grid">
          ${vars.map(v => `
            <label>${esc(v.label || v.name)}
              <input data-config="${esc(v.name)}" type="${v.secret ? "password" : "text"}" value="${esc((project.config_values || {})[v.name] || "")}" placeholder="${esc(v.placeholder || v.name)}">
            </label>
          `).join("")}
        </div>
      `;
    }

    function render() {
      const f = state.filter.trim().toLowerCase();
      const projects = state.projects.filter(p => {
        const hay = [p.name, p.category, p.purpose, p.usage, p.path].join(" ").toLowerCase();
        return !f || hay.includes(f);
      });
      renderSummary(state.projects);
      if (!projects.length) {
        $("#projects").innerHTML = `<div class="empty">没有匹配的项目。</div>`;
        return;
      }
      $("#projects").innerHTML = projects.map(project => `
        <article class="project" data-pid="${esc(project.id)}">
          <div class="project-head">
            <div class="title-row">
              <div>
                <h2>${esc(project.name)}</h2>
                <div class="category">${esc(project.category)}</div>
              </div>
              <span class="status ${projectRunning(project) ? "running" : ""}">${projectRunning(project) ? "运行中" : "空闲"}</span>
            </div>
            <div class="path">${esc(project.path)}</div>
          </div>
          <div class="body">
            <div class="desc">${esc(project.purpose)}</div>
            <div>
              <div class="section-title">使用方法</div>
              <div class="desc">${esc(project.usage)}</div>
            </div>
            <div>
              <div class="section-title">启动步骤</div>
              <ol class="steps">${(project.startup_steps || []).map(s => `<li>${esc(s)}</li>`).join("")}</ol>
            </div>
            <div>
              <div class="section-title">配置参数</div>
              ${configHtml(project)}
            </div>
            <div>
              <div class="section-title">启动项与控制台</div>
              <div class="commands">${project.commands.map(c => commandHtml(project, c)).join("")}</div>
            </div>
            <div class="save-row">
              <button class="warning" data-action="save-project">保存配置和命令</button>
              <button data-action="readme">查看 README</button>
              <button data-action="open-path">打开目录</button>
              <button data-action="open-cmd">打开 CMD</button>
              ${(project.links || []).map(l => `<a class="link-button" href="${esc(l.url)}" target="_blank" rel="noreferrer">${esc(l.label)}</a>`).join("")}
              <span class="muted" id="msg-${esc(project.id)}"></span>
            </div>
          </div>
        </article>
      `).join("");
    }

    async function load() {
      state.projects = (await api("/api/projects")).projects;
      render();
    }

    function findProject(pid) {
      return state.projects.find(p => p.id === pid);
    }

    function collectProject(pid) {
      const card = document.querySelector(`.project[data-pid="${CSS.escape(pid)}"]`);
      const project = findProject(pid);
      const config_values = {};
      card.querySelectorAll("[data-config]").forEach(input => config_values[input.dataset.config] = input.value);
      const commands = project.commands.map(cmd => {
        const row = card.querySelector(`.command[data-cid="${CSS.escape(cmd.id)}"]`);
        return {
          id: cmd.id,
          label: cmd.label,
          cwd: cmd.cwd,
          command: row.querySelector("[data-field='command']").value,
          url: cmd.url || ""
        };
      });
      return { config_values, commands };
    }

    async function saveProject(pid) {
      const msg = $(`#msg-${CSS.escape(pid)}`);
      msg.textContent = "保存中...";
      await api(`/api/projects/${encodeURIComponent(pid)}/save`, {
        method: "POST",
        body: JSON.stringify(collectProject(pid))
      });
      msg.textContent = "已保存";
      await load();
      setTimeout(() => { const m = $(`#msg-${CSS.escape(pid)}`); if (m) m.textContent = ""; }, 1800);
    }

    async function commandAction(pid, cid, action) {
      if (action === "start") await saveProject(pid);
      await api(`/api/projects/${encodeURIComponent(pid)}/commands/${encodeURIComponent(cid)}/${action}`, { method: "POST", body: "{}" });
      await load();
    }

    async function showReadme(pid) {
      const data = await api(`/api/projects/${encodeURIComponent(pid)}/readme`);
      $("#readmeTitle").textContent = `${data.project_name} README${data.generated ? "（已自动生成）" : ""}`;
      $("#readmePath").textContent = data.path || "";
      $("#readmeContent").textContent = data.content || "README 为空。";
      $("#readmeModal").classList.add("open");
    }

    async function refreshLogs() {
      for (const project of state.projects) {
        for (const cmd of project.commands) {
          const term = document.getElementById(`term-${project.id}-${cmd.id}`);
          if (!term) continue;
          try {
            const data = await api(`/api/logs?project=${encodeURIComponent(project.id)}&command=${encodeURIComponent(cmd.id)}`);
            const text = (data.logs || []).join("");
            if (term.textContent !== text) {
              const nearBottom = term.scrollTop + term.clientHeight >= term.scrollHeight - 20;
              term.textContent = text || "等待输出...";
              if (nearBottom) term.scrollTop = term.scrollHeight;
            }
          } catch {}
        }
      }
    }

    document.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const action = btn.dataset.action;
      try {
        if (btn.id === "refresh") return await load();
        const projectEl = btn.closest(".project");
        if (!projectEl) return;
        const pid = projectEl.dataset.pid;
        if (action === "save-project") return await saveProject(pid);
        if (action === "readme") return await showReadme(pid);
        if (action === "open-path") return await api(`/api/projects/${encodeURIComponent(pid)}/open`, { method: "POST", body: "{}" });
        if (action === "open-cmd") return await api(`/api/projects/${encodeURIComponent(pid)}/cmd`, { method: "POST", body: "{}" });
        const cmdEl = btn.closest(".command");
        if (cmdEl && action) return await commandAction(pid, cmdEl.dataset.cid, action);
      } catch (err) {
        alert(err.message);
      }
    });

    $("#search").addEventListener("input", (e) => {
      state.filter = e.target.value;
      render();
    });
    $("#closeReadme").addEventListener("click", () => $("#readmeModal").classList.remove("open"));
    $("#readmeModal").addEventListener("click", (e) => {
      if (e.target.id === "readmeModal") $("#readmeModal").classList.remove("open");
    });

    function userEditing() {
      const el = document.activeElement;
      return el && ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName);
    }

    load();
    renderExternalSites();
    setInterval(() => { if (!userEditing()) load(); }, 5000);
    setInterval(refreshLogs, 1200);
  </script>
</body>
</html>
"""


class ProcessState:
    def __init__(self) -> None:
        self.process: subprocess.Popen[Any] | None = None
        self.logs: deque[str] = deque(maxlen=900)
        self.started_at: float | None = None
        self.lock = threading.Lock()

    def append(self, line: str) -> None:
        with self.lock:
            stamp = time.strftime("%H:%M:%S")
            self.logs.append(f"[{stamp}] {line}")

    def snapshot(self) -> list[str]:
        with self.lock:
            return list(self.logs)


processes: dict[tuple[str, str], ProcessState] = {}
config_lock = threading.Lock()


def read_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        cfg = {"projects": {project["id"]: {"config_values": {}, "commands": project["commands"]} for project in DEFAULT_PROJECTS}}
        write_config(cfg)
        return cfg
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = CONFIG_PATH.with_suffix(".broken.json")
        CONFIG_PATH.replace(backup)
        cfg = {"projects": {project["id"]: {"config_values": {}, "commands": project["commands"]} for project in DEFAULT_PROJECTS}}
        write_config(cfg)
        return cfg


def write_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def merged_projects() -> list[dict[str, Any]]:
    cfg = read_config()
    saved_projects = cfg.setdefault("projects", {})
    projects: list[dict[str, Any]] = []
    changed = False
    for default in DEFAULT_PROJECTS:
        project = deepcopy(default)
        saved = saved_projects.setdefault(project["id"], {})
        if "config_values" not in saved:
            saved["config_values"] = {}
            changed = True
        if "commands" not in saved:
            saved["commands"] = project["commands"]
            changed = True
        command_overrides = {cmd["id"]: cmd for cmd in saved.get("commands", [])}
        merged_commands = []
        for cmd in project["commands"]:
            merged = {**cmd, **command_overrides.get(cmd["id"], {})}
            state = processes.setdefault((project["id"], merged["id"]), ProcessState())
            proc = state.process
            running = proc is not None and proc.poll() is None
            merged["status"] = {"running": running, "pid": proc.pid if running and proc else None}
            merged["logs"] = state.snapshot()[-80:]
            merged_commands.append(merged)
        project["commands"] = merged_commands
        project["config_values"] = saved.get("config_values", {})
        projects.append(project)
    if changed:
        write_config(cfg)
    return projects


def find_project(project_id: str) -> dict[str, Any] | None:
    return next((p for p in merged_projects() if p["id"] == project_id), None)


def find_command(project: dict[str, Any], command_id: str) -> dict[str, Any] | None:
    return next((c for c in project["commands"] if c["id"] == command_id), None)


def find_readme(project: dict[str, Any]) -> Path | None:
    root = Path(project["path"])
    if not root.exists():
        return None
    for name in README_CANDIDATES:
        candidate = root / name
        if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    readmes = sorted(
        [item for item in root.iterdir() if item.is_file() and item.name.lower().startswith("readme") and item.stat().st_size > 0],
        key=lambda item: item.name.lower(),
    )
    return readmes[0] if readmes else None


def read_text_flexible(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", locale.getpreferredencoding(False)):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def readme_target(project: dict[str, Any]) -> Path:
    root = Path(project["path"])
    for name in ("README.md", "README.zh-CN.md", "README.zh.md", "使用说明.md"):
        candidate = root / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return root / "README.md"


def build_generated_readme(project: dict[str, Any]) -> str:
    lines = [
        f"# {project['name']}",
        "",
        "## 项目概览",
        "",
        f"- 项目路径：`{project['path']}`",
        f"- 项目类型：{project.get('category', '未分类')}",
        f"- 用途：{project.get('purpose', '待补充')}",
        "",
        "## 使用方法",
        "",
        project.get("usage") or "待补充。",
        "",
        "## 启动步骤",
        "",
    ]
    for index, step in enumerate(project.get("startup_steps") or ["待补充"], start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "## 启动命令", ""])
    for command in project.get("commands") or []:
        lines.extend(
            [
                f"### {command.get('label') or command.get('id')}",
                "",
                f"- 工作目录：`{command.get('cwd') or project['path']}`",
                "",
                "```powershell",
                command.get("command") or "",
                "```",
                "",
            ]
        )
        if command.get("url"):
            lines.extend([f"- 访问地址：{command['url']}", ""])
    config_vars = project.get("config_vars") or []
    if config_vars:
        lines.extend(["## 配置参数", ""])
        for var in config_vars:
            suffix = "（敏感信息）" if var.get("secret") else ""
            lines.append(f"- `{var['name']}`：{var.get('label') or var['name']}{suffix}")
        lines.append("")
    links = project.get("links") or []
    if links:
        lines.extend(["## 常用链接", ""])
        for link in links:
            lines.append(f"- [{link.get('label') or link['url']}]({link['url']})")
        lines.append("")
    lines.extend(
        [
            "## 备注",
            "",
            "本文档由 `stock_manager` 的 Py Project Hub 自动生成，可继续手动补充更详细的项目说明。",
            "",
        ]
    )
    return "\n".join(lines)


def get_or_create_readme(project: dict[str, Any]) -> dict[str, Any]:
    existing = find_readme(project)
    if existing:
        return {"path": str(existing), "content": read_text_flexible(existing), "generated": False}
    root = Path(project["path"])
    if not root.exists():
        raise ValueError(f"项目目录不存在: {root}")
    target = readme_target(project)
    content = build_generated_readme(project)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "content": content, "generated": True}


def process_key(project_id: str, command_id: str) -> tuple[str, str]:
    return project_id, command_id


def decode_output(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030", locale.getpreferredencoding(False)):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def reader_thread(state: ProcessState, proc: subprocess.Popen[Any]) -> None:
    try:
        assert proc.stdout is not None
        for raw in iter(proc.stdout.readline, b""):
            if not raw:
                break
            state.append(decode_output(raw))
    except Exception as exc:
        state.append(f"日志读取失败: {exc}\n")
    finally:
        code = proc.poll()
        if code is None:
            code = proc.wait()
        state.append(f"进程结束，退出码 {code}\n")


def start_command(project_id: str, command_id: str) -> None:
    project = find_project(project_id)
    if not project:
        raise ValueError("项目不存在")
    command = find_command(project, command_id)
    if not command:
        raise ValueError("启动项不存在")
    key = process_key(project_id, command_id)
    state = processes.setdefault(key, ProcessState())
    if state.process and state.process.poll() is None:
        raise ValueError("该启动项已经在运行")

    cwd = Path(command.get("cwd") or project["path"])
    if not cwd.exists():
        raise ValueError(f"工作目录不存在: {cwd}")

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    for name, value in (project.get("config_values") or {}).items():
        if value not in (None, ""):
            env[name] = str(value)

    cmd = command.get("command", "").strip()
    if not cmd:
        raise ValueError("启动命令为空")

    state.append(f"$ {cmd}\n")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        bufsize=1,
        creationflags=creationflags,
    )
    state.process = proc
    state.started_at = time.time()
    threading.Thread(target=reader_thread, args=(state, proc), daemon=True).start()


def stop_command(project_id: str, command_id: str) -> None:
    state = processes.setdefault(process_key(project_id, command_id), ProcessState())
    proc = state.process
    if not proc or proc.poll() is not None:
        state.append("没有正在运行的进程。\n")
        return
    state.append("正在停止进程...\n")
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
    state.append("停止命令已发送。\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "ProjectHub/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self) -> None:
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.send_html()
            elif parsed.path == "/api/projects":
                self.send_json({"projects": merged_projects()})
            elif len(parts := [unquote(x) for x in parsed.path.strip("/").split("/") if x]) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "readme":
                project = find_project(parts[2])
                if not project:
                    raise ValueError("项目不存在")
                payload = get_or_create_readme(project)
                payload["project_name"] = project["name"]
                self.send_json(payload)
            elif parsed.path == "/api/logs":
                qs = parse_qs(parsed.query)
                project_id = qs.get("project", [""])[0]
                command_id = qs.get("command", [""])[0]
                state = processes.setdefault(process_key(project_id, command_id), ProcessState())
                self.send_json({"logs": state.snapshot()})
            else:
                self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        parts = [unquote(x) for x in parsed.path.strip("/").split("/") if x]
        try:
            if len(parts) == 4 and parts[:1] == ["api"] and parts[1] == "projects" and parts[3] == "save":
                project_id = parts[2]
                body = self.read_body()
                with config_lock:
                    cfg = read_config()
                    entry = cfg.setdefault("projects", {}).setdefault(project_id, {})
                    entry["config_values"] = body.get("config_values", {})
                    if "commands" in body:
                        entry["commands"] = body["commands"]
                    write_config(cfg)
                self.send_json({"ok": True})
                return

            if len(parts) == 4 and parts[:1] == ["api"] and parts[1] == "projects" and parts[3] == "open":
                project = find_project(parts[2])
                if not project:
                    raise ValueError("项目不存在")
                path = project["path"]
                if os.name == "nt":
                    os.startfile(path)  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(["xdg-open", path])
                self.send_json({"ok": True})
                return

            if len(parts) == 4 and parts[:1] == ["api"] and parts[1] == "projects" and parts[3] == "cmd":
                project = find_project(parts[2])
                if not project:
                    raise ValueError("项目不存在")
                path = Path(project["path"])
                if not path.exists():
                    raise ValueError(f"项目目录不存在: {path}")
                if os.name != "nt":
                    raise ValueError("当前按钮仅支持 Windows cmd.exe")
                subprocess.Popen(
                    ["cmd.exe", "/K", f'cd /d "{path}"'],
                    cwd=str(path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                self.send_json({"ok": True})
                return

            if len(parts) == 6 and parts[:1] == ["api"] and parts[1] == "projects" and parts[3] == "commands":
                project_id, command_id, action = parts[2], parts[4], parts[5]
                if action == "start":
                    start_command(project_id, command_id)
                elif action == "stop":
                    stop_command(project_id, command_id)
                elif action == "clear":
                    processes.setdefault(process_key(project_id, command_id), ProcessState()).logs.clear()
                else:
                    raise ValueError("未知操作")
                self.send_json({"ok": True})
                return

            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


def main() -> None:
    read_config()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Project Hub running at {url}")
    if os.environ.get("PROJECT_HUB_NO_BROWSER") != "1":
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Project Hub...")
    finally:
        for project_id, command_id in list(processes):
            try:
                stop_command(project_id, command_id)
            except Exception:
                pass
        server.server_close()


if __name__ == "__main__":
    main()
