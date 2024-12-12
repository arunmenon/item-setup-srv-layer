# models/models.py

from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship
import json
from sqlalchemy.types import TypeDecorator

from datetime import datetime
from .database import Base

# JSON TypeDecorator for storing JSON data in TEXT fields
class JSONEncodedDict(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        return json.loads(value)
    
class ModelFamily(Base):
    __tablename__ = 'model_families'
    model_family_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    generation_prompt_templates = relationship('GenerationPromptTemplate', back_populates='model_family')
    evaluation_prompt_templates = relationship('EvaluationPromptTemplate', back_populates='model_family')

# Association Tables
generation_task_evaluation_tasks = Table('generation_task_evaluation_tasks', Base.metadata,
    Column('generation_task_id', Integer, ForeignKey('generation_tasks.task_id'), primary_key=True),
    Column('evaluation_task_id', Integer, ForeignKey('evaluation_tasks.task_id'), primary_key=True)
)

generation_task_providers = Table('generation_task_providers', Base.metadata,
    Column('generation_task_id', Integer, ForeignKey('generation_tasks.task_id'), primary_key=True),
    Column('provider_id', Integer, ForeignKey('providers.provider_id'), primary_key=True)
)

class GenerationTask(Base):
    __tablename__ = 'generation_tasks'
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    max_tokens  = Column(Integer)
    output_format = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    prompt_templates = relationship('GenerationPromptTemplate', back_populates='generation_task', cascade='all, delete-orphan')
    evaluation_tasks = relationship('EvaluationTask', secondary=generation_task_evaluation_tasks, back_populates='generation_tasks')
    providers = relationship('ProviderConfig', secondary=generation_task_providers, back_populates='generation_tasks')

class EvaluationTask(Base):
    __tablename__ = 'evaluation_tasks'
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    max_tokens = Column(Integer)
    output_format = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    expected_metrics = Column(JSONEncodedDict)  
    prompt_templates = relationship('EvaluationPromptTemplate', back_populates='evaluation_task', cascade='all, delete-orphan')
    generation_tasks = relationship('GenerationTask', secondary=generation_task_evaluation_tasks, back_populates='evaluation_tasks')

class GenerationPromptTemplate(Base):
    __tablename__ = 'generation_prompt_templates'
    template_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('generation_tasks.task_id'), nullable=False)
    model_family_id = Column(Integer, ForeignKey('model_families.model_family_id'), nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    placeholders = Column(JSONEncodedDict, nullable=True)  # Add this line

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    generation_task = relationship('GenerationTask', back_populates='prompt_templates')
    model_family = relationship('ModelFamily', back_populates='generation_prompt_templates')

class EvaluationPromptTemplate(Base):
    __tablename__ = 'evaluation_prompt_templates'
    template_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('evaluation_tasks.task_id'), nullable=False)
    model_family_id = Column(Integer, ForeignKey('model_families.model_family_id'), nullable=False)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    placeholders = Column(JSONEncodedDict, nullable=True)  # Add this line

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    evaluation_task = relationship('EvaluationTask', back_populates='prompt_templates')
    model_family = relationship('ModelFamily', back_populates='evaluation_prompt_templates')

class ProviderConfig(Base):
    __tablename__ = 'providers'

    provider_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    provider_name = Column(String, nullable=False)  # e.g., 'openai'
    family = Column(String, nullable=False)         # e.g., 'gpt', 'llama'
    model = Column(String, nullable=False)
    version = Column(String, nullable=False)
    api_base = Column(String, nullable=False)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    generation_tasks = relationship('GenerationTask', secondary=generation_task_providers, back_populates='providers')

class StylingGuide(Base):
    __tablename__ = 'styling_guides'

    styling_guide_id = Column(Integer, primary_key=True)
    product_type = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('product_type', 'task_name', 'version', name='_product_task_version_uc'),
    )

class TaskExecutionConfig(Base):
    __tablename__ = 'task_execution_config'

    config_id = Column(Integer, primary_key=True)
    default_tasks = Column(JSONEncodedDict, nullable=False)
    conditional_tasks = Column(JSONEncodedDict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AEInclusionList(Base):
    __tablename__ = 'ae_inclusion_list'

    id = Column(Integer, primary_key=True)
    product_type = Column(String, nullable=False)
    attribute_name = Column(String, nullable=False)
    certified = Column(Boolean, default=False)
    attribute_precision_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('product_type', 'attribute_name', name='_pt_attr_uc'),
    )    

class PostProcessHooksConfig(Base):
    __tablename__ = 'post_process_hooks_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_task_name = Column(String, ForeignKey('generation_tasks.task_name'), nullable=False)
    hook_type = Column(String, nullable=False)  # e.g. 'guardrail' or 'custom'
    class_path = Column(String, nullable=False) # e.g. 'some.module.GuardrailClass' or 'my_hooks.ConformityCheckHook'
    parameters = Column(JSONEncodedDict, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Potential relationship to GenerationTask if needed
    # generation_task = relationship('GenerationTask', backref='post_process_hooks')
