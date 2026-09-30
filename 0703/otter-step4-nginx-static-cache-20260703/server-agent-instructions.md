# 给服务器 Agent 的执行说明

目标：修复 `play.otterlantis.com` 静态资源响应头，改善 Three.js / WebGL 大资源的缓存、MIME 和跨域配置。

这一步只改 Nginx 静态资源配置，不改 Python 后端，不重启后端服务。

## 1. 放置配置

把 `play-otterlantis-static-cache.include.conf` 的内容放进 `play.otterlantis.com` 对应的 Nginx `server { ... }` 配置块中，并放在通用 `location / { ... }` 之前。

如果使用宝塔面板，请进入该站点的 Nginx 配置页，把这段配置粘贴到该站点的 `server` 配置里。

## 2. 检查并重载

执行：

```bash
nginx -t
systemctl reload nginx
```

如果 `nginx -t` 不通过，不要 reload，把错误信息发回。

## 3. 部署后验证

在服务器或任意可访问公网的机器上执行：

```bash
./verify-step4-headers.sh https://play.otterlantis.com
```

也可以手动检查：

```bash
curl -I https://play.otterlantis.com/index.html
curl -I https://play.otterlantis.com/assets/SectionParkour-Ba-Fk1Jk.js
curl -I https://play.otterlantis.com/model-site/scene-terrain-opt.glb
```

期望看到：

```text
index.html:
Cache-Control: no-cache, must-revalidate

assets/*.js, assets/*.css:
Cache-Control: public, max-age=31536000, immutable

*.glb:
Content-Type: model/gltf-binary
Cache-Control: public, max-age=2592000
Access-Control-Allow-Origin: *
```

## 4. 如果首访仍然慢

这份配置主要改善缓存、MIME 和重复加载。若首次访问仍然慢，说明瓶颈在源站带宽或线路，下一步应把 `.glb`、`.webp` 和大 JS chunk 迁移到对象存储 + CDN。

## 5. 注意

不要在报告里粘贴宝塔账号、服务器密码、环境变量文件、数据库文件或任何密钥。
