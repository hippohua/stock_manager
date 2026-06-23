# Py Project Hub

这是一个本地项目启动面板，用来集中管理 `D:\py project` 下每天要看的项目。

## 启动

```powershell
cd "D:\py project\stock_manager"
python project_hub.py
```

默认访问地址：

```text
http://127.0.0.1:5066
```

如需换端口：

```powershell
$env:PROJECT_HUB_PORT="5070"
python project_hub.py
```

## 功能

- 以板块形式展示项目名称、路径、用途、使用方法和启动步骤
- 每个项目可配置一个或多个启动项
- 每个启动项都有启动、停止、清屏、打开链接和独立控制台日志
- 支持在页面中修改启动命令
- 支持填写 API key、端口、Webhook 等配置参数
- 配置参数会作为环境变量传给启动的项目进程

## 配置文件

首次启动后会自动生成：

```text
D:\py project\stock_manager\dashboard_config.json
```

页面中保存的命令和参数都会写入这个文件，不会直接改动各个项目目录。

## 注意

- Node/Vite 项目需要本机已有 `npm`，并且项目依赖已安装。
- Streamlit 项目需要本机已有 `streamlit`。
- Python 项目如果缺依赖，控制台会显示对应报错；进入项目目录安装依赖后重新启动即可。
- 前后端分离项目一般需要分别启动后端和前端两个启动项。
