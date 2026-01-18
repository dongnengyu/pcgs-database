# PCGS Coin Database

## 项目概述

PCGS硬币数据库是一个用于管理和抓取PCGS硬币认证数据的Web应用程序。

## 技术栈

- **后端**: FastAPI + Python 3.11+
- **数据库**: SQLite
- **爬虫**: Playwright
- **前端**: 原生HTML/CSS/JavaScript
- **配置**: pydantic-settings

## 项目结构

```
pcgs_database/
├── src/pcgs_database/      # Python包
│   ├── config.py           # 配置管理（环境变量）
│   ├── database.py         # 数据库操作
│   ├── main.py             # FastAPI应用入口
│   ├── models.py           # Pydantic模型
│   ├── scraper.py          # PCGS爬虫
│   └── routers/            # API路由
│       └── coins.py        # 硬币相关API
├── static/                 # 静态文件
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── data/                   # 数据目录（git忽略内容）
│   ├── pcgs_coins.db       # SQLite数据库
│   └── images/             # 硬币图片
└── tests/                  # 测试目录
```

## 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 运行应用
python -m src.pcgs_database.main

# 应用访问地址
http://localhost:47568
```

## 环境变量

可通过 `.env` 文件或环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| HOST | 0.0.0.0 | 服务器主机 |
| PORT | 47568 | 服务器端口 |
| DEBUG | false | 调试模式 |

## API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| GET | `/api/coins` | 获取所有硬币 |
| GET | `/api/coins/{cert_number}` | 获取单个硬币 |
| POST | `/api/scrape` | 抓取硬币数据 |
| DELETE | `/api/coins/{cert_number}` | 删除硬币 |

## 代码规范

- 使用 `logging` 而非 `print()`
- 所有函数添加类型注解
- 使用 pydantic 模型进行数据验证
- FastAPI 使用 `lifespan` 而非已弃用的 `on_event`

## 数据库表结构

`coins` 表字段：
- `id`: 主键
- `cert_number`: PCGS证书号（唯一）
- `pcgs_number`: PCGS编号
- `grade`: 等级
- `date_mintmark`: 日期/铸造标记
- `denomination`: 面额
- `price_guide_value`: 价格指南值
- `population`: 存世量
- `pop_higher`: 更高等级存世量
- `mintage`: 铸造量
- `local_image_path`: 本地图片路径
- `created_at`: 创建时间
- `updated_at`: 更新时间
