# 本地启动方式
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
