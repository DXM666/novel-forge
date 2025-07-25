"""
数据库模型定义 - 使用SQLAlchemy ORM
提供所有数据库表的模型定义和关系
"""
import uuid
import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, 
    DateTime, ForeignKey, JSON, Table, UniqueConstraint,
    Index, create_engine
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# 创建基类
Base = declarative_base()

# 定义关联表
character_event = Table(
    'character_event',
    Base.metadata,
    Column('character_id', UUID(as_uuid=True), ForeignKey('characters.id'), primary_key=True),
    Column('event_id', UUID(as_uuid=True), ForeignKey('events.id'), primary_key=True),
    Column('role', String(50)),  # 角色在事件中的角色，如"主角"、"配角"等
    Column('created_at', DateTime, default=datetime.datetime.utcnow)
)

# 定义关联表
location_event = Table(
    'location_event',
    Base.metadata,
    Column('location_id', UUID(as_uuid=True), ForeignKey('locations.id'), primary_key=True),
    Column('event_id', UUID(as_uuid=True), ForeignKey('events.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow)
)

class Project(Base):
    """项目表"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    author_id = Column(String(255), nullable=False)  # 可以关联到用户表
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="project", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="project", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="project", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    memory_entries = relationship("MemoryEntry", back_populates="project", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_projects_author_id', 'author_id'),
    )


class Character(Base):
    """角色表"""
    __tablename__ = 'characters'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50))  # 如"protagonist", "antagonist"等
    description = Column(Text)
    attributes = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="characters")
    events = relationship("Event", secondary=character_event, back_populates="characters")
    
    # 索引
    __table_args__ = (
        Index('idx_characters_project_id', 'project_id'),
        Index('idx_characters_name', 'name'),
    )


class Location(Base):
    """地点表"""
    __tablename__ = 'locations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    attributes = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="locations")
    events = relationship("Event", secondary=location_event, back_populates="locations")
    
    # 索引
    __table_args__ = (
        Index('idx_locations_project_id', 'project_id'),
        Index('idx_locations_name', 'name'),
    )


class Item(Base):
    """物品表"""
    __tablename__ = 'items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    attributes = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="items")
    
    # 索引
    __table_args__ = (
        Index('idx_items_project_id', 'project_id'),
        Index('idx_items_name', 'name'),
    )


class Event(Base):
    """事件表"""
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_time = Column(String(255))  # 事件发生的时间（可以是具体时间或相对描述）
    attributes = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="events")
    characters = relationship("Character", secondary=character_event, back_populates="events")
    locations = relationship("Location", secondary=location_event, back_populates="locations")
    
    # 索引
    __table_args__ = (
        Index('idx_events_project_id', 'project_id'),
    )


class Rule(Base):
    """世界规则表"""
    __tablename__ = 'rules'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    attributes = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="rules")
    
    # 索引
    __table_args__ = (
        Index('idx_rules_project_id', 'project_id'),
    )


class Chapter(Base):
    """章节表"""
    __tablename__ = 'chapters'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    status = Column(String(50), default='draft')  # draft, published, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="chapters")
    scenes = relationship("Scene", back_populates="chapter", cascade="all, delete-orphan")
    
    # 索引和约束
    __table_args__ = (
        Index('idx_chapters_project_id', 'project_id'),
        UniqueConstraint('project_id', 'chapter_number', name='uq_chapter_number'),
    )


class Scene(Base):
    """场景表"""
    __tablename__ = 'scenes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    scene_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    chapter = relationship("Chapter", back_populates="scenes")
    
    # 索引和约束
    __table_args__ = (
        Index('idx_scenes_chapter_id', 'chapter_id'),
        UniqueConstraint('chapter_id', 'scene_number', name='uq_scene_number'),
    )


class Outline(Base):
    """大纲表"""
    __tablename__ = 'outlines'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, unique=True)
    skeleton = Column(Text)  # 故事骨架
    structure = Column(JSONB)  # 结构化大纲信息
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_outlines_project_id', 'project_id'),
    )


class MemoryEntry(Base):
    """记忆条目表"""
    __tablename__ = 'memory_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    entry_type = Column(String(50), nullable=False)  # summary, event, character_state等
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="memory_entries")
    vector_memory = relationship("VectorMemory", back_populates="memory_entry", uselist=False, cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_memory_entries_project_id', 'project_id'),
        Index('idx_memory_entries_type', 'entry_type'),
    )


class VectorMemory(Base):
    """向量记忆表"""
    __tablename__ = 'vector_memories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey('memory_entries.id'), nullable=False, unique=True)
    embedding = Column(ARRAY(Float))  # 向量嵌入
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 关系
    memory_entry = relationship("MemoryEntry", back_populates="vector_memory")
    
    # 索引
    __table_args__ = (
        Index('idx_vector_memories_memory_id', 'memory_id'),
    )


class VersionHistory(Base):
    """版本历史表"""
    __tablename__ = 'version_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # memory, element, graph等
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 索引和约束
    __table_args__ = (
        Index('idx_version_history_entity', 'entity_type', 'entity_id'),
        Index('idx_version_history_project_id', 'project_id'),
        UniqueConstraint('entity_type', 'entity_id', 'version', name='uq_version'),
    )


class GraphState(Base):
    """LangGraph状态表"""
    __tablename__ = 'graph_states'
    
    thread_id = Column(String(255), primary_key=True)
    state = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# 数据库连接和会话
def get_engine(url=None):
    """获取数据库引擎"""
    if url is None:
        url = f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:" \
              f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@" \
              f"{os.environ.get('POSTGRES_HOST', 'localhost')}:" \
              f"{os.environ.get('POSTGRES_PORT', '5432')}/" \
              f"{os.environ.get('POSTGRES_DB', 'novel_forge')}"
    
    return create_engine(url)

def get_session_maker(engine=None):
    """获取会话工厂"""
    if engine is None:
        engine = get_engine()
    
    return sessionmaker(bind=engine)

def init_db(engine=None):
    """初始化数据库"""
    if engine is None:
        engine = get_engine()
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    return engine
