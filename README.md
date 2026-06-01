# 本地启动方式

## 一键启动（前端 + 沙箱 + 后端）

```bash
bash scripts/dev.sh
```

默认地址：

- 前端: http://localhost:3000
- 后端: http://localhost:8008
- 后端文档: http://localhost:8008/docs
- OpenSandbox: http://localhost:8080

脚本会自动创建后端虚拟环境、安装缺失依赖、启动 OpenSandbox、后端和前端。日志输出在 `logs/dev/`。

也可以通过环境变量覆盖前后端端口：

```bash
FRONTEND_PORT=3001 BACKEND_PORT=8009 bash scripts/dev.sh
```

---

## 分别启动

  后端

   ## 1. 进入后端目录
   cd ./aiteacher/ai-teacher-backend

   ## 2. 创建虚拟环境（可选但推荐）
   python3 -m venv venv
   
   source venv/bin/activate  # macOS/Linux

   ## 3. 安装依赖
   pip install -r requirements.txt

   ## 4. 配置环境变量（在 .env 文件中设置）
   ## ZHIPU_API_KEY=your-api-key

   ## 5. 启动服务
   python run.py
   ## 或
   uvicorn app.main:app --reload --port 8008

  后端运行在: http://localhost:8008

  ---

  前端

   ## 1. 进入前端目录
   cd ./aiteacher/ai-teacher-frontend

   ## 2. 安装依赖
   npm install

   ## 3. 启动开发服务器
   npm run dev

  前端运行在: http://localhost:3000

  ---
