# 线上部署（Docker）

## 1. 部署前准备

服务器需要安装 Docker Engine 和 Docker Compose Plugin，并开放 `80/443`。Compose 默认仅将 API 的 `28080` 绑定到服务器本机，由 Nginx 对外转发。

将 `server` 目录上传到服务器，然后创建运行环境文件：

```bash
cd /opt/slack-off-api
cp .env.production.example .env.production
chmod 600 .env.production
```

填写 `.env.production` 的 MySQL 账号、密码和随机 `TOKEN_SECRET`。不要把 `.env.production` 提交到仓库或复制到镜像中。

数据库账号必须允许线上服务器 IP 连接 `slack-off`，并具备 `wx_mini_user` 的 `SELECT/INSERT/UPDATE` 权限以及 `system_config` 的 `SELECT` 权限。

`system_config` 内以下配置必须为启用状态：

| 配置键 | 用途 |
| --- | --- |
| `WECHAT_APP_ID` | 小程序登录 |
| `WECHAT_APP_SECRET` | 小程序登录 |
| `TENCENT_COS_BUCKET` | COS 桶名称 |
| `TENCENT_COS_SECRET_ID` | COS 密钥 ID |
| `TENCENT_COS_SECRET_KEY` | COS 密钥 |
| `TENCENT_COS_DOMAIN` | COS 访问域名 |
| `TENCENT_COS_REGION` | COS 区域 |

## 2. 构建并运行

```bash
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:28080/
```

健康检查返回 HTTP 200 即服务可用。查看日志：

```bash
docker compose logs -f api
```

更新版本：

```bash
docker compose up -d --build
```

## 3. Nginx 与 HTTPS

将 `deploy/nginx.conf.example` 复制到服务器 Nginx 配置目录并替换 `api.example.com`，检查后重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

随后使用 Certbot 为域名签发证书，并在 HTTPS server 块中保留相同的反向代理配置。生产环境不要直接暴露 `28080` 到公网；只允许本机 Nginx 访问它。

## 4. 小程序上线配置

在微信公众平台添加 API 域名为 request 合法域名，并将 `TENCENT_COS_DOMAIN` 添加为 download 合法域名。前端 `wx-app/utils/request.js` 的小程序 `BASE_URL` 也应改为 `https://api.example.com`，不可再使用 `127.0.0.1`。

## 5. 常用运维命令

```bash
docker compose restart api
docker compose logs --tail=200 api
docker compose down
```
