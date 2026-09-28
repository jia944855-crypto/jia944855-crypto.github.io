# Santorini Tourism Website — Static Preview

Translation practice project · static HTML mirror prepared for GitHub Pages

- **原站**：https://santorini.gr/ （英文版，无官方中文版本，符合作业「选取的外文网站不存在中文版本」要求）
- **主页**：`index.html`（本地服务器地址为 `/`）
- **近似版备份**：`index-approx-backup.html`
- **四个栏目页**：`/about-santorini/`、`/attractions/`、`/what-to-do/`、`/what-to-eat/`
- **本地子页面**：每个页面单独保存在对应目录的 `index.html` 中，例如 `/history/`、`/churches/`、`/archaeolog/`。
- **旧地址兼容**：根目录原有的 `*.html` 地址会跳转到对应的 `/页面名/` 路由。
- **批量处理脚本**：`scripts/normalize_local_routes.py`（默认预览；首次执行需传 `--apply`）。

---

## 本地预览

请使用本地服务器打开，以启用与原站一致的目录路由（在项目文件夹里执行）：

```bash
python3 -m http.server 8777
```

然后浏览器访问 `http://localhost:8777/`。例如：

- `http://localhost:8777/churches/`
- `http://localhost:8777/archaeolog/`
- `http://localhost:8777/history/`

## 发布到 GitHub Pages

这是静态 HTML/CSS/JavaScript 网站，不需要 Node.js 或后端服务即可发布。

推荐把仓库命名为 `你的用户名.github.io`，然后在 GitHub 仓库的 **Settings → Pages** 中选择：

- **Source**：Deploy from a branch
- **Branch**：`main`
- **Folder**：`/ (root)`

发布后网址为：`https://你的用户名.github.io/`。

项目中的 `node_modules/`、备份文件、翻译表格和检查图片已加入 `.gitignore`，不会被提交；网站运行所需的 HTML、图片、CSS、JavaScript 以及 `wp-content/`、`wp-includes/` 静态资源会保留。

注意：GitHub Pages 只能托管静态文件。天气接口、WordPress AJAX/API、后台表单等依赖服务器的功能不会在 GitHub Pages 上运行；页面主体和本地静态资源可以正常预览。

---

## ⚠️ 交作业前必须改的地方

打开本地服务器首页可查看镜像。页面继续使用独立页面文件；批处理脚本将页面链接统一到本地目录路由，并从导航菜单移除了 Blog 和 How to Get Here。页面图片、样式和交互脚本仍由项目内保存的资源提供。

后续应基于这份完整英文镜像进行中文翻译，不要再以旧的手工近似版为翻译底稿。

---

## 文件结构

```
翻译项目/
├── index.html                  原站首页 HTML 镜像
├── index-approx-backup.html    之前的手工近似版备份
├── about-santorini/index.html  About Santorini 子页面
├── attractions/index.html     Attractions 子页面
├── churches/index.html        Churches 子页面
├── archaeolog/index.html      Archaeological 子页面
├── history/index.html         History 子页面
├── scripts/normalize_local_routes.py
├── route-migration-backup-20260922/  路由调整前的 HTML 备份
├── assets/images/              早期整理的图片素材
├── wp-content/                 原站 CSS、JS、字体和图片资源
├── wp-includes/                原站公共脚本资源
└── reference/
    ├── original-content.md     原文抓取记录 + 原站设计规格（配色/字体/板块对照）
    └── 预览全页.png             整页预览截图
```

---

## 当前版本说明

当前 `index.html` 直接采用原站首页的完整英文文案、DOM 结构和资源引用，并已在项目中保存原站 CSS、JavaScript、图片和字体相关资源：

- 主页面包含原站完整导航和首页交互。
- 本地子页面通过 `/页面名/` 路由访问；原 `.html` 地址保留兼容跳转。
- 原站核心图片、页面专属 CSS、主题 CSS、Elementor/Slick/菜单等脚本已抓取到本地资源目录。
- 中文翻译和语料库替换暂未开始。

---

## 后续要做的（按作业要求）

- [ ] 根据英语—中文语料库制作对照版
- [ ] 初稿打包提交：9月29日（周二）前交给学委
- [ ] 终稿上传「悦怿网」https://joytransyueyi.cn 「旅游」栏目 → 文字投稿 → 网页转 PDF 或图片：10月9日（周五）前
- [ ] 评论区附上原网站链接和译制网页链接

格式参考样例：https://joytransyueyi.cn/articleDetails?id=85
