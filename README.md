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
