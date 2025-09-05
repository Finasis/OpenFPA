from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# ============================================
# IMPORT TEMPLATE SCHEMAS
# ============================================

class ImportTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str  # 'csv', 'excel', 'json', 'api', 'database'
    target_entity: str  # 'gl_transactions', 'budget_lines', 'kpis', etc.
    file_format: Dict[str, Any] = {}
    mapping_rules: Dict[str, Any] = {}
    transformation_rules: Dict[str, Any] = {}
    validation_rules: Dict[str, Any] = {}
    default_values: Dict[str, Any] = {}
    is_active: bool = True

class ImportTemplateCreate(ImportTemplateBase):
    company_id: UUID
    created_by: Optional[UUID] = None

class ImportTemplateUpdate(ImportTemplateBase):
    pass

class ImportTemplateResponse(ImportTemplateBase):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# FIELD MAPPING SCHEMAS
# ============================================

class FieldMappingBase(BaseModel):
    source_field: str
    target_table: str
    target_field: str
    field_order: Optional[int] = None
    data_type: Optional[str] = None  # 'string', 'number', 'date', 'boolean'
    transformation_type: Optional[str] = 'direct'  # 'direct', 'lookup', 'formula', 'concatenate', 'split'
    transformation_config: Dict[str, Any] = {}
    is_required: bool = False
    default_value: Optional[str] = None
    validation_regex: Optional[str] = None
    error_handling: str = 'reject'  # 'reject', 'skip', 'default'

class FieldMappingCreate(FieldMappingBase):
    pass

class FieldMappingUpdate(FieldMappingBase):
    pass

class FieldMappingResponse(FieldMappingBase):
    id: UUID
    template_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# MAPPING LOOKUP SCHEMAS
# ============================================

class MappingLookupBase(BaseModel):
    lookup_type: str  # 'account', 'cost_center', 'vendor', 'customer', 'project'
    external_code: str
    internal_id: UUID
    internal_code: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_active: bool = True

class MappingLookupCreate(MappingLookupBase):
    company_id: UUID

class MappingLookupUpdate(BaseModel):
    internal_id: Optional[UUID] = None
    internal_code: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class MappingLookupResponse(MappingLookupBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# IMPORT JOB SCHEMAS
# ============================================

class ImportJobBase(BaseModel):
    job_name: Optional[str] = None
    status: str  # 'pending', 'validating', 'processing', 'completed', 'failed', 'partial'
    source_file_path: Optional[str] = None
    source_file_size: Optional[int] = None
    total_records: Optional[int] = None
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0

class ImportJobResponse(ImportJobBase):
    id: UUID
    template_id: Optional[UUID]
    template_name: Optional[str]
    company_id: UUID
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_summary: Optional[Dict[str, Any]]
    import_config: Optional[Dict[str, Any]]
    executed_by: Optional[UUID]
    executed_by_email: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# IMPORT EXECUTION SCHEMAS
# ============================================

class ImportPreviewResponse(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    preview_data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

class ImportExecuteResponse(BaseModel):
    job_id: str
    status: str
    total_records: int
    successful_records: int
    failed_records: int
    skipped_records: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

class ImportJobDetailResponse(BaseModel):
    id: UUID
    import_job_id: UUID
    row_number: int
    source_data: Dict[str, Any]
    transformed_data: Optional[Dict[str, Any]]
    status: str  # 'success', 'failed', 'skipped'
    error_message: Optional[str]
    warnings: Optional[Dict[str, Any]]
    created_entity_id: Optional[UUID]
    created_entity_type: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# IMPORT SCHEDULE SCHEMAS
# ============================================

class ImportScheduleBase(BaseModel):
    schedule_name: str
    schedule_type: str  # 'once', 'daily', 'weekly', 'monthly', 'custom'
    cron_expression: Optional[str] = None
    source_config: Dict[str, Any] = {}
    is_active: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3
    notification_emails: List[str] = []

class ImportScheduleCreate(ImportScheduleBase):
    template_id: UUID
    created_by: Optional[UUID] = None

class ImportScheduleUpdate(ImportScheduleBase):
    pass

class ImportScheduleResponse(ImportScheduleBase):
    id: UUID
    template_id: UUID
    last_run_time: Optional[datetime]
    next_run_time: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# DATA SOURCE CONNECTION SCHEMAS
# ============================================

class DataSourceConnectionBase(BaseModel):
    connection_name: str
    connection_type: str  # 'database', 'api', 'ftp', 'sftp', 's3'
    connection_config: Dict[str, Any]  # Encrypted connection details
    test_query: Optional[str] = None
    is_active: bool = True

class DataSourceConnectionCreate(DataSourceConnectionBase):
    company_id: UUID
    created_by: Optional[UUID] = None

class DataSourceConnectionUpdate(BaseModel):
    connection_config: Optional[Dict[str, Any]] = None
    test_query: Optional[str] = None
    is_active: Optional[bool] = None

class DataSourceConnectionResponse(DataSourceConnectionBase):
    id: UUID
    company_id: UUID
    last_tested_at: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ============================================
# TRANSFORMATION & VALIDATION RULE SCHEMAS
# ============================================

class TransformationRuleBase(BaseModel):
    rule_name: str
    rule_type: str  # 'regex', 'formula', 'lookup', 'script'
    rule_definition: str
    input_parameters: Dict[str, Any] = {}
    output_format: Optional[str] = None
    description: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    is_system_rule: bool = False

class TransformationRuleCreate(TransformationRuleBase):
    company_id: UUID
    created_by: Optional[UUID] = None

class TransformationRuleResponse(TransformationRuleBase):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ValidationRuleBase(BaseModel):
    rule_name: str
    rule_type: str  # 'required', 'format', 'range', 'lookup', 'custom'
    field_type: Optional[str] = None  # 'account', 'amount', 'date', 'code'
    validation_logic: str
    error_message: Optional[str] = None
    severity: str = 'error'  # 'error', 'warning', 'info'
    is_system_rule: bool = False

class ValidationRuleCreate(ValidationRuleBase):
    company_id: UUID
    created_by: Optional[UUID] = None

class ValidationRuleResponse(ValidationRuleBase):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True