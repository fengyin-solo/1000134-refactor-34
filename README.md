# 冷链物流温控运营平台

面向冷链订单、运单、冷藏车、温控监控、冷库仓储与结算的一体化运营后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/            每个业务模块一个页面
│   ├── src/api/              统一请求封装
│   ├── src/stores/           会话与筛选状态
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/          每个业务模块一组接口
│   ├── app/services/         业务规则与状态流转
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8000/api/health`

启动流程统一在 `app/bootstrap.py`：启动时读取运行环境与必要配置（非法配置
启动即失败），随后装载示例数据并执行自检，自检摘要同时打到启动日志。健康检查
与启动日志共用同一套自检口径，返回运行环境、模块数量与示例数据状态：

```json
{"ok": true, "env": "local", "modules": 21,
 "seed": {"state": "pristine", "modules": 21, "rows": 63, "seed_rows": 63}}
```

示例数据被改脏（新增、修改、清空）后，`seed.state` 会变成 `dirty` / `empty`，
调用重置入口即可恢复，重置后会按启动流程再做一次自检：

```bash
curl -X POST http://127.0.0.1:8000/api/seed/reset
```

可用环境变量（默认值对应本地开发，不设任何变量时流程与原来一致）：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `local` | 运行环境，可选 `local`、`dev`、`staging`、`prod` |
| `APP_PORT` | `8000` | 服务端口，需在 1-65535 内 |
| `APP_NAME` | 冷链物流温控运营平台 | 应用名称，不能为空 |
| `APP_ALLOWED_ORIGINS` | 本地两个 5173 来源 | CORS 来源，逗号分隔，必须是 http(s) 地址 |

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 冷链订单 | `order` | 冷链订单 | 订单编号、客户名称、货物名称 |
| 运单管理 | `waybill` | 冷链运单 | 运单号、关联订单、承运车辆 |
| 冷藏车管理 | `vehicle` | 冷藏车辆 | 车牌号码、车辆类型、制冷机组型号 |
| 司机管理 | `driver` | 司机档案 | 司机工号、司机姓名、联系电话 |
| 温控监控 | `temperature` | 温控记录 | 记录编号、关联运单、测点编号 |
| 温度异常 | `excursion` | 温度异常事件 | 事件编号、关联运单、异常类型 |
| 冷库管理 | `warehouse` | 冷库档案 | 冷库编码、冷库名称、库区温区 |
| 入库管理 | `inbound` | 入库单 | 入库单号、供应商名称、货物名称 |
| 出库管理 | `outbound` | 出库单 | 出库单号、客户名称、货物名称 |
| 库存管理 | `inventory` | 库存批次 | 库存编码、货物名称、批次号 |
| 批次追溯 | `trace` | 追溯记录 | 追溯码、货物名称、生产批次 |
| 质检管理 | `quality` | 质检单 | 质检单号、关联批次、检测项目 |
| 线路管理 | `route` | 配送线路 | 线路编码、线路名称、起点冷库 |
| 调度派单 | `dispatch` | 调度单 | 调度单号、关联订单、配送线路 |
| 温控设备 | `device` | 温控设备 | 设备编号、设备名称、设备型号 |
| 维保工单 | `maint` | 维保工单 | 工单编号、关联设备、故障现象 |
| 告警中心 | `alarm` | 告警事件 | 告警编号、告警类型、告警等级 |
| 客户管理 | `customer` | 客户档案 | 客户编码、客户名称、客户类型 |
| 计费结算 | `billing` | 计费单 | 计费单号、客户名称、计费周期 |
| 报表导出 | `report` | 报表任务 | 报表名称、统计范围、统计周期 |
| 系统设置 | `setting` | 系统参数 | 参数编码、参数名称、参数值 |

## 约定

- 每个模块的前端页面在 `frontend/src/views/<模块>/index.vue`，后端接口在
  `backend/app/routers/<模块>.py`，业务规则在 `backend/app/services/<模块>.py`。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。
