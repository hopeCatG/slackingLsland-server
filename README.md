## 创建虚拟环境

python -m venv .venv

## 激活虚拟环境

### Windows：

.venv\Scripts\activate

### Linux / Mac：

source .venv/bin/activate

## 安装依赖

pip install -r requirements.txt

## 启动服务

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

微信登录接口 `POST /api/v1/auth/wechat/login` 会从已启用的 `system_config` 记录读取 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`，并调用微信 `jscode2session` 获取真实 OpenID。

通用静态图片上传接口为 `POST /api/v1/storage/upload?directory=uploads`（multipart 字段名 `file`，目录可选 `uploads`、`images`、`avatars`）；头像上传接口为 `POST /api/v1/storage/avatar`。COS 配置从已启用的 `system_config` 读取：`TENCENT_COS_BUCKET`、`TENCENT_COS_SECRET_ID`、`TENCENT_COS_SECRET_KEY`、`TENCENT_COS_DOMAIN`、`TENCENT_COS_REGION`。

聊天搭子模块先执行 `sql/20260828_create_chat_companion_tables.sql`，再将 `system_config.DIFY_CHAT_API_KEY` 替换为 Dify 对话应用的真实 App API Key。服务端通过 `/api/v1/chat-companion` 代理 Dify SSE，前端不接触密钥。生产环境建议将 `DIFY_CHAT_BASE_URL` 配置为 HTTPS 地址。
