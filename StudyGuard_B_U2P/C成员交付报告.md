# StudyGuard C 成员交付报告

## 交付范围

本次交付完成 README 第 15.1 节中 C 成员负责的 U2P 端界面、HTTP 管理与系统集成工作：

- E5/本地管理页面
- 管理员手机端 HTTP 服务
- 座位状态查询、清除占座、强制释放
- 温湿度与 BAD_ENV 展示
- 临时离开超时时间修改
- C2 接收、状态机、HTTP 服务和界面的统一入口集成

## 新增文件

```text
config.py
  U2P 管理端默认配置

admin_api.py
  UI/HTTP 调用的管理接口封装

http_server.py
  HTTP API 与手机端/E5 Web 管理页面

ui_touch.py
  E5 本地浏览器/触摸页面启动辅助

C成员交付报告.md
  本文档
```

## 修改文件

```text
main.py
  从 B 成员最小演示入口升级为系统集成入口：
  - 启动 C2 接收
  - 启动座位状态机
  - 启动 HTTP 管理服务
  - 可选打开 E5 本地管理页面
  - 用锁保护状态机并发访问
```

## HTTP 接口

接口与总计划 README 第 8.3 节保持一致：

```text
GET  /api/seats
GET  /api/seats/A01
POST /api/seats/A01/clear
POST /api/seats/A01/release
GET  /api/env
POST /api/config/timeout
```

`/` 提供手机端和 E5 都可访问的管理页面，页面会每秒刷新座位、环境和配置状态。

## 运行方式

U2P 接 C2 后运行：

```bash
python3 main.py --port /dev/ttyS2 --seat A01 --http-port 8080
python3 main.py --port /dev/ttyS2 --seat A01,A02 --http-host 0.0.0.0 --http-port 8080
```

如果要在 E5 本地打开页面：

```bash
DISPLAY=:0 XAUTHORITY=/home/sunrise/.Xauthority xdg-open http://127.0.0.1:8080/studyguard.html
```

## 验收点

1. 管理员手机连接同一局域网后，访问 `http://172.20.10.6:8080/` 能看到座位状态。
2. U1P 经 C2 上传 `HUMAN/RFID/ENV/HB` 后，页面状态能自动刷新。
3. ENV 超出阈值时，页面显示 `BAD_ENV`。
4. 座位进入 `OCCUPY` 后，手机端可以点击“清除占座”。
5. 任意非空座位可以通过“强制释放”回到 `EMPTY`。
6. 修改离开超时时间后，后续 `AWAY -> OCCUPY` 计时按新值执行。
