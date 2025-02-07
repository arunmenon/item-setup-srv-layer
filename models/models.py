# models/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ProviderConfig(Base):
    __tablename__ = "providers"
    provider_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    provider_name = Column(String, nullable=False)
    family = Column(String, nullable=False)
    model = Column(String, nullable=False)
    version = Column(String, nullable=False)
    api_base = Column(String, nullable=False)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class GenerationTask(Base):
    __tablename__ = "generation_tasks"
    task_id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    max_tokens = Column(Integer)
    output_format = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class EvaluationTask(Base):
    __tablename__ = "evaluation_tasks"
    task_id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    max_tokens = Column(Integer)
    output_format = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class TaskExecutionConfig(Base):
    __tablename__ = "task_execution_config"
    config_id = Column(Integer, primary_key=True, index=True)
    default_tasks = Column(Text, nullable=False)  # Stored as JSON string
    conditional_tasks = Column(Text, nullable=False)  # Stored as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class StylingGuide(Base):
    __tablename__ = "styling_guides"
    styling_guide_id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('product_type', 'task_name', name='_prod_task_uc'),)

class GenerationPromptTemplate(Base):
    __tablename__ = "generation_prompt_templates"
    template_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("generation_tasks.task_id"), nullable=False)
    model_family_id = Column(Integer, nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class EvaluationPromptTemplate(Base):
    __tablename__ = "evaluation_prompt_templates"
    template_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("evaluation_tasks.task_id"), nullable=False)
    model_family_id = Column(Integer, nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
