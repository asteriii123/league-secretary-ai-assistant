# 前端应用

`frontend` 是团支书 AI 助手的 Vue 3 前端，负责团支书端和学生端的页面、交互、状态管理以及后端 API 调用。

## 目录说明

```text
frontend/
├── src/
│   ├── api/          # 鉴权、对话、通知、收集、知识库等 API 封装
│   ├── components/   # 全局布局和可复用 Vue 组件
│   ├── views/        # 登录、工作台、AI 对话、通知、收集和知识库页面
│   ├── router/       # Vue Router 路由和角色访问守卫
│   ├── stores/       # Pinia 登录状态和用户信息
│   ├── styles/       # 全局样式和响应式布局
│   ├── App.vue       # 前端根组件
│   └── main.ts       # Vue 应用启动入口
├── package.json      # 依赖和 npm 脚本
└── vite.config.ts    # Vite 开发与构建配置
```

## 开发启动

```powershell
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>。开发时需同时启动 `backend` 中的 FastAPI 服务。

## 质量检查

```powershell
npm run type-check
npm run build
```

完整安装、配置和使用方法请查看 [项目根目录 README](../README.md)。
