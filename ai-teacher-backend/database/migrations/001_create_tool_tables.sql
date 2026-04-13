-- 教学图片库表
-- 用于存储教学图片资源,支持向量检索
CREATE TABLE IF NOT EXISTS teaching_image_library (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR(50) UNIQUE NOT NULL,
    image_url TEXT,
    svg_code TEXT,
    description TEXT NOT NULL,
    
    -- 标签和分类
    knowledge_points TEXT[],  -- 关联知识点ID数组
    modality VARCHAR(50),     -- 图片类型: infographic, proof_diagram等
    difficulty VARCHAR(20),   -- 难度: easy, medium, hard
    
    -- 适用场景
    applicable_phases INTEGER[],  -- 适用教学阶段
    teaching_modes TEXT[],        -- 适用教学模式
    
    -- 元数据
    tags TEXT[],
    template_id VARCHAR(50),      -- 模板ID(如果是模板生成)
    created_by VARCHAR(20),       -- template/ai_generated/manual
    quality_score FLOAT,          -- 质量评分 0-1
    usage_count INTEGER DEFAULT 0,
    
    -- 向量嵌入(用于语义检索)
    embedding VECTOR(1536),       -- OpenAI embedding维度
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引
CREATE INDEX IF NOT EXISTS idx_image_embedding ON teaching_image_library 
USING ivfflat (embedding vector_cosine_ops);

-- 创建知识点索引
CREATE INDEX IF NOT EXISTS idx_image_kp ON teaching_image_library USING GIN(knowledge_points);

-- 创建modality索引
CREATE INDEX IF NOT EXISTS idx_image_modality ON teaching_image_library(modality);

-- 创建created_by索引
CREATE INDEX IF NOT EXISTS idx_image_created_by ON teaching_image_library(created_by);


-- 教学视频库表(未来扩展)
CREATE TABLE IF NOT EXISTS teaching_video_library (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(50) UNIQUE NOT NULL,
    video_url TEXT NOT NULL,
    description TEXT NOT NULL,
    
    -- 标签和分类
    knowledge_points TEXT[],
    video_type VARCHAR(50),       -- 视频类型: demo, lecture, practice等
    duration INTEGER,             -- 时长(秒)
    
    -- 适用场景
    applicable_phases INTEGER[],
    teaching_modes TEXT[],
    
    -- 元数据
    tags TEXT[],
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建知识点索引
CREATE INDEX IF NOT EXISTS idx_video_kp ON teaching_video_library USING GIN(knowledge_points);


-- 交互演示库表(未来扩展)
CREATE TABLE IF NOT EXISTS teaching_interactive_library (
    id SERIAL PRIMARY KEY,
    demo_id VARCHAR(50) UNIQUE NOT NULL,
    demo_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,        -- 演示配置
    description TEXT NOT NULL,
    
    -- 标签和分类
    knowledge_points TEXT[],
    
    -- 适用场景
    applicable_phases INTEGER[],
    teaching_modes TEXT[],
    
    -- 元数据
    tags TEXT[],
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建知识点索引
CREATE INDEX IF NOT EXISTS idx_interactive_kp ON teaching_interactive_library USING GIN(knowledge_points);


-- 工具使用记录表(用于分析和优化)
CREATE TABLE IF NOT EXISTS tool_usage_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    student_id INTEGER NOT NULL,
    kp_id VARCHAR(20) NOT NULL,
    
    -- 工具信息
    tool_name VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    params JSONB,
    
    -- 结果
    success BOOLEAN NOT NULL,
    resource_id VARCHAR(50),
    error_message TEXT,
    
    -- 性能
    execution_time_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_student ON tool_usage_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_tool ON tool_usage_logs(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usage_created ON tool_usage_logs(created_at);


-- 注释
COMMENT ON TABLE teaching_image_library IS '教学图片库 - 存储教学图片资源,支持向量检索';
COMMENT ON TABLE teaching_video_library IS '教学视频库 - 存储教学视频资源';
COMMENT ON TABLE teaching_interactive_library IS '交互演示库 - 存储交互式教学演示';
COMMENT ON TABLE tool_usage_logs IS '工具使用记录 - 用于分析和优化工具调用';
