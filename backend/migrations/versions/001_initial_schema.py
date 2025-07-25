"""初始数据库架构

Revision ID: 001
Revises: 
Create Date: 2025-05-15 23:23:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建项目表
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('author_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_projects_author_id', 'projects', ['author_id'])
    
    # 创建角色表
    op.create_table(
        'characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50)),
        sa.Column('description', sa.Text()),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_characters_project_id', 'characters', ['project_id'])
    op.create_index('idx_characters_name', 'characters', ['name'])
    
    # 创建地点表
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_locations_project_id', 'locations', ['project_id'])
    op.create_index('idx_locations_name', 'locations', ['name'])
    
    # 创建物品表
    op.create_table(
        'items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_items_project_id', 'items', ['project_id'])
    op.create_index('idx_items_name', 'items', ['name'])
    
    # 创建事件表
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('event_time', sa.String(255)),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_events_project_id', 'events', ['project_id'])
    
    # 创建角色-事件关联表
    op.create_table(
        'character_event',
        sa.Column('character_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('characters.id'), primary_key=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id'), primary_key=True),
        sa.Column('role', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # 创建地点-事件关联表
    op.create_table(
        'location_event',
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id'), primary_key=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # 创建世界规则表
    op.create_table(
        'rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_rules_project_id', 'rules', ['project_id'])
    
    # 创建章节表
    op.create_table(
        'chapters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('content', sa.Text()),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_chapters_project_id', 'chapters', ['project_id'])
    op.create_unique_constraint('uq_chapter_number', 'chapters', ['project_id', 'chapter_number'])
    
    # 创建场景表
    op.create_table(
        'scenes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chapters.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('content', sa.Text()),
        sa.Column('scene_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_scenes_chapter_id', 'scenes', ['chapter_id'])
    op.create_unique_constraint('uq_scene_number', 'scenes', ['chapter_id', 'scene_number'])
    
    # 创建大纲表
    op.create_table(
        'outlines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False, unique=True),
        sa.Column('skeleton', sa.Text()),
        sa.Column('structure', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_outlines_project_id', 'outlines', ['project_id'])
    
    # 创建记忆条目表
    op.create_table(
        'memory_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('entry_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_memory_entries_project_id', 'memory_entries', ['project_id'])
    op.create_index('idx_memory_entries_type', 'memory_entries', ['entry_type'])
    
    # 创建向量记忆表
    op.create_table(
        'vector_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('memory_entries.id'), nullable=False, unique=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float())),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_vector_memories_memory_id', 'vector_memories', ['memory_id'])
    
    # 创建版本历史表
    op.create_table(
        'version_history',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index('idx_version_history_entity', 'version_history', ['entity_type', 'entity_id'])
    op.create_index('idx_version_history_project_id', 'version_history', ['project_id'])
    op.create_unique_constraint('uq_version', 'version_history', ['entity_type', 'entity_id', 'version'])
    
    # 创建LangGraph状态表
    op.create_table(
        'graph_states',
        sa.Column('thread_id', sa.String(255), primary_key=True),
        sa.Column('state', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # 创建向量索引
    op.execute(
        """
        -- 确保pg_vector扩展已安装
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- 为向量记忆表添加向量索引
        ALTER TABLE vector_memories ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);
        
        -- 创建更新向量的触发器函数
        CREATE OR REPLACE FUNCTION update_embedding_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.embedding_vector = NEW.embedding::vector;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- 创建触发器
        CREATE TRIGGER update_vector_memories_embedding_vector
        BEFORE INSERT OR UPDATE ON vector_memories
        FOR EACH ROW
        EXECUTE FUNCTION update_embedding_vector();
        
        -- 创建向量索引
        CREATE INDEX IF NOT EXISTS idx_vector_memories_embedding_vector ON vector_memories USING ivfflat (embedding_vector vector_cosine_ops);
        """
    )


def downgrade():
    # 删除表（按照依赖关系的反序）
    op.drop_table('graph_states')
    op.drop_table('version_history')
    op.drop_table('vector_memories')
    op.drop_table('memory_entries')
    op.drop_table('outlines')
    op.drop_table('scenes')
    op.drop_table('chapters')
    op.drop_table('location_event')
    op.drop_table('character_event')
    op.drop_table('rules')
    op.drop_table('events')
    op.drop_table('items')
    op.drop_table('locations')
    op.drop_table('characters')
    op.drop_table('projects')
    
    # 删除向量索引和扩展
    op.execute(
        """
        DROP TRIGGER IF EXISTS update_vector_memories_embedding_vector ON vector_memories;
        DROP FUNCTION IF EXISTS update_embedding_vector();
        """
    )
