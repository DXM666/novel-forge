-- 小说创作记忆系统数据库初始化脚本
-- 基于PostgreSQL + 向量数据库设计

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- 启用向量扩展（如果使用PostgreSQL的pg_vector扩展）
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. 项目表（小说项目）
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    author_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 记忆条目表（短期和长期记忆）
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    entry_type VARCHAR(50) NOT NULL, -- summary, event, character_state, plot_point, worldbuilding
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 向量记忆表（用于语义搜索）
CREATE TABLE IF NOT EXISTS vector_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID REFERENCES memory_entries(id) ON DELETE CASCADE,
    embedding VECTOR(1536), -- 假设使用OpenAI的embedding维度
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 小说元素表（角色、地点、物品等）
CREATE TABLE IF NOT EXISTS novel_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- character, location, item, rule
    element_id VARCHAR(100) NOT NULL, -- 用户定义的ID，如 'protagonist', 'magic_castle'
    data JSONB NOT NULL, -- 存储元素的详细信息
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, element_type, element_id)
);

-- 5. 图状态表（知识图谱状态）
CREATE TABLE IF NOT EXISTS graph_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    graph_data JSONB NOT NULL, -- 存储图数据（节点和边）
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. 版本历史表（用于版本控制）
CREATE TABLE IF NOT EXISTS version_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, -- 'memory', 'element', 'graph'
    entity_id UUID NOT NULL, -- 引用memory_entries.id或novel_elements.id或graph_states.id
    version_data JSONB NOT NULL, -- 存储该版本的完整数据
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_comment TEXT
);

-- 7. 章节表
CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    content TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, in_progress, completed, revised
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, chapter_number)
);

-- 8. 场景表
CREATE TABLE IF NOT EXISTS scenes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    title VARCHAR(255),
    summary TEXT,
    content TEXT,
    location_id VARCHAR(100), -- 引用novel_elements中的location
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chapter_id, scene_number)
);

-- 9. 场景-角色关联表
CREATE TABLE IF NOT EXISTS scene_characters (
    scene_id UUID REFERENCES scenes(id) ON DELETE CASCADE,
    character_id VARCHAR(100) NOT NULL, -- 引用novel_elements中的character
    role VARCHAR(50), -- protagonist, antagonist, supporting
    PRIMARY KEY (scene_id, character_id)
);

-- 10. 大纲表
CREATE TABLE IF NOT EXISTS outlines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    skeleton TEXT, -- 故事骨架
    structure JSONB, -- 存储结构化的大纲信息
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. 大纲章节表
CREATE TABLE IF NOT EXISTS outline_chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outline_id UUID REFERENCES outlines(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title VARCHAR(255),
    summary TEXT,
    scenes JSONB, -- 存储场景列表
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(outline_id, chapter_number)
);

-- 创建索引以提高查询性能
CREATE INDEX idx_memory_entries_project_id ON memory_entries(project_id);
CREATE INDEX idx_memory_entries_entry_type ON memory_entries(entry_type);
CREATE INDEX idx_novel_elements_project_id ON novel_elements(project_id);
CREATE INDEX idx_novel_elements_type_id ON novel_elements(project_id, element_type, element_id);
CREATE INDEX idx_chapters_project_id ON chapters(project_id);
CREATE INDEX idx_scenes_chapter_id ON scenes(chapter_id);

-- 创建向量索引（如果使用pg_vector）
CREATE INDEX idx_vector_memories_embedding ON vector_memories USING ivfflat (embedding vector_cosine_ops);

-- 创建触发器函数：自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要自动更新updated_at的表添加触发器
CREATE TRIGGER update_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_entries_updated_at
BEFORE UPDATE ON memory_entries
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_novel_elements_updated_at
BEFORE UPDATE ON novel_elements
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_graph_states_updated_at
BEFORE UPDATE ON graph_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chapters_updated_at
BEFORE UPDATE ON chapters
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenes_updated_at
BEFORE UPDATE ON scenes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_outlines_updated_at
BEFORE UPDATE ON outlines
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_outline_chapters_updated_at
BEFORE UPDATE ON outline_chapters
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建视图：项目摘要视图
CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.id AS project_id,
    p.title,
    p.description,
    p.author_id,
    COUNT(DISTINCT c.id) AS chapter_count,
    COUNT(DISTINCT s.id) AS scene_count,
    COUNT(DISTINCT ne.id) AS element_count,
    MAX(c.updated_at) AS last_updated
FROM 
    projects p
LEFT JOIN 
    chapters c ON p.id = c.project_id
LEFT JOIN 
    scenes s ON c.id = s.chapter_id
LEFT JOIN 
    novel_elements ne ON p.id = ne.project_id
GROUP BY 
    p.id, p.title, p.description, p.author_id;

-- 创建视图：最近记忆视图
CREATE OR REPLACE VIEW recent_memories AS
SELECT 
    me.id,
    me.project_id,
    me.entry_type,
    me.content,
    me.metadata,
    me.created_at
FROM 
    memory_entries me
WHERE 
    me.created_at > (NOW() - INTERVAL '7 days')
ORDER BY 
    me.created_at DESC;

-- 创建函数：获取相关记忆
CREATE OR REPLACE FUNCTION get_related_memories(
    p_project_id UUID,
    p_query TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    memory_id UUID,
    entry_type VARCHAR(50),
    content TEXT,
    metadata JSONB,
    similarity FLOAT
) AS $$
DECLARE
    query_embedding VECTOR(1536);
BEGIN
    -- 这里假设有一个函数可以获取embedding，实际实现可能需要调用外部API
    -- query_embedding := get_embedding(p_query);
    
    RETURN QUERY
    SELECT 
        me.id AS memory_id,
        me.entry_type,
        me.content,
        me.metadata,
        1 - (vm.embedding <=> query_embedding) AS similarity
    FROM 
        memory_entries me
    JOIN 
        vector_memories vm ON me.id = vm.memory_id
    WHERE 
        me.project_id = p_project_id
    ORDER BY 
        similarity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 注释：
-- 1. 此脚本假设使用PostgreSQL 13+和pg_vector扩展
-- 2. 向量搜索功能需要实际的embedding函数实现
-- 3. 可能需要根据实际部署环境调整索引和向量维度