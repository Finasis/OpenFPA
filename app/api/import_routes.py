from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import io
import csv
import pandas as pd
from datetime import datetime

from app.models.base import get_db
from app.services.import_module import ImportEngine, MappingService, ValidationService
from app.schemas.import_schemas import (
    ImportTemplateCreate,
    ImportTemplateResponse,
    FieldMappingCreate,
    FieldMappingResponse,
    MappingLookupCreate,
    MappingLookupResponse,
    ImportJobResponse,
    ImportPreviewResponse,
    ImportExecuteResponse
)

router = APIRouter(prefix="/api/v1/import", tags=["Import"])

# ============================================
# IMPORT TEMPLATES
# ============================================

@router.post("/templates", response_model=ImportTemplateResponse)
async def create_import_template(
    template: ImportTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new import template"""
    
    validation_service = ValidationService(db)
    
    # Validate template configuration
    validation_result = await validation_service.validate_import_template(template.dict())
    if not validation_result['is_valid']:
        raise HTTPException(status_code=400, detail={
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings']
        })
    
    # Create template in database
    query = """
    INSERT INTO import_templates (
        id, company_id, name, description, source_type,
        target_entity, file_format, mapping_rules,
        transformation_rules, validation_rules, default_values,
        is_active, created_by, created_at
    ) VALUES (
        gen_random_uuid(), :company_id, :name, :description, :source_type,
        :target_entity, :file_format, :mapping_rules,
        :transformation_rules, :validation_rules, :default_values,
        :is_active, :created_by, :created_at
    ) RETURNING *
    """
    
    result = db.execute(query, {
        'company_id': template.company_id,
        'name': template.name,
        'description': template.description,
        'source_type': template.source_type,
        'target_entity': template.target_entity,
        'file_format': json.dumps(template.file_format),
        'mapping_rules': json.dumps(template.mapping_rules),
        'transformation_rules': json.dumps(template.transformation_rules),
        'validation_rules': json.dumps(template.validation_rules),
        'default_values': json.dumps(template.default_values),
        'is_active': template.is_active,
        'created_by': template.created_by,
        'created_at': datetime.utcnow()
    })
    
    db.commit()
    return result.fetchone()

@router.get("/templates", response_model=List[ImportTemplateResponse])
async def list_import_templates(
    company_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List import templates for a company"""
    
    query = """
    SELECT * FROM import_templates
    WHERE company_id = :company_id
    """
    
    if active_only:
        query += " AND is_active = true"
    
    query += " ORDER BY name"
    
    result = db.execute(query, {'company_id': company_id})
    return [dict(row) for row in result.fetchall()]

@router.get("/templates/{template_id}", response_model=ImportTemplateResponse)
async def get_import_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific import template"""
    
    query = "SELECT * FROM import_templates WHERE id = :template_id"
    result = db.execute(query, {'template_id': template_id})
    template = result.fetchone()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return dict(template)

# ============================================
# FIELD MAPPINGS
# ============================================

@router.post("/templates/{template_id}/mappings", response_model=FieldMappingResponse)
async def create_field_mapping(
    template_id: UUID,
    mapping: FieldMappingCreate,
    db: Session = Depends(get_db)
):
    """Create a field mapping for a template"""
    
    query = """
    INSERT INTO field_mappings (
        id, template_id, source_field, target_table, target_field,
        field_order, data_type, transformation_type, transformation_config,
        is_required, default_value, validation_regex, error_handling,
        created_at
    ) VALUES (
        gen_random_uuid(), :template_id, :source_field, :target_table, :target_field,
        :field_order, :data_type, :transformation_type, :transformation_config,
        :is_required, :default_value, :validation_regex, :error_handling,
        :created_at
    ) RETURNING *
    """
    
    result = db.execute(query, {
        'template_id': template_id,
        'source_field': mapping.source_field,
        'target_table': mapping.target_table,
        'target_field': mapping.target_field,
        'field_order': mapping.field_order,
        'data_type': mapping.data_type,
        'transformation_type': mapping.transformation_type,
        'transformation_config': json.dumps(mapping.transformation_config),
        'is_required': mapping.is_required,
        'default_value': mapping.default_value,
        'validation_regex': mapping.validation_regex,
        'error_handling': mapping.error_handling,
        'created_at': datetime.utcnow()
    })
    
    db.commit()
    return result.fetchone()

@router.get("/templates/{template_id}/mappings", response_model=List[FieldMappingResponse])
async def list_field_mappings(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """List field mappings for a template"""
    
    query = """
    SELECT * FROM field_mappings
    WHERE template_id = :template_id
    ORDER BY field_order
    """
    
    result = db.execute(query, {'template_id': template_id})
    return [dict(row) for row in result.fetchall()]

# ============================================
# MAPPING LOOKUPS
# ============================================

@router.post("/lookups", response_model=MappingLookupResponse)
async def create_mapping_lookup(
    lookup: MappingLookupCreate,
    db: Session = Depends(get_db)
):
    """Create a mapping lookup entry"""
    
    mapping_service = MappingService(db)
    
    lookup_id = await mapping_service.create_mapping_lookup(
        company_id=lookup.company_id,
        lookup_type=lookup.lookup_type,
        external_code=lookup.external_code,
        internal_id=lookup.internal_id,
        description=lookup.description
    )
    
    return {
        'id': lookup_id,
        'company_id': lookup.company_id,
        'lookup_type': lookup.lookup_type,
        'external_code': lookup.external_code,
        'internal_id': lookup.internal_id,
        'description': lookup.description
    }

@router.get("/lookups", response_model=List[MappingLookupResponse])
async def list_mapping_lookups(
    company_id: UUID,
    lookup_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List mapping lookups"""
    
    query = """
    SELECT * FROM mapping_lookups
    WHERE company_id = :company_id
    """
    
    params = {'company_id': company_id}
    
    if lookup_type:
        query += " AND lookup_type = :lookup_type"
        params['lookup_type'] = lookup_type
    
    query += " ORDER BY lookup_type, external_code"
    
    result = db.execute(query, params)
    return [dict(row) for row in result.fetchall()]

@router.post("/lookups/bulk")
async def bulk_create_mapping_lookups(
    company_id: UUID = Form(...),
    lookup_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Bulk create mapping lookups from CSV file"""
    
    # Read CSV file
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # Expected columns: external_code, internal_id, description (optional)
    if 'external_code' not in df.columns or 'internal_id' not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain 'external_code' and 'internal_id' columns"
        )
    
    mapping_service = MappingService(db)
    created_count = 0
    errors = []
    
    for _, row in df.iterrows():
        try:
            await mapping_service.create_mapping_lookup(
                company_id=str(company_id),
                lookup_type=lookup_type,
                external_code=str(row['external_code']),
                internal_id=str(row['internal_id']),
                description=row.get('description')
            )
            created_count += 1
        except Exception as e:
            errors.append({
                'external_code': row['external_code'],
                'error': str(e)
            })
    
    return {
        'created': created_count,
        'errors': errors
    }

# ============================================
# IMPORT EXECUTION
# ============================================

@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    template_id: UUID = Form(...),
    company_id: UUID = Form(...),
    user_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Preview import without saving to database"""
    
    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        contents = await file.read()
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name
    
    try:
        import_engine = ImportEngine(db)
        
        # Run import in dry-run mode
        result = await import_engine.process_import(
            template_id=str(template_id),
            company_id=str(company_id),
            file_path=tmp_file_path,
            user_id=str(user_id),
            dry_run=True
        )
        
        return ImportPreviewResponse(
            total_records=result['total_records'],
            valid_records=result['successful_records'],
            invalid_records=result['failed_records'],
            preview_data=result.get('preview_data', []),
            errors=result.get('errors', []),
            warnings=result.get('warnings', [])
        )
        
    finally:
        # Clean up temporary file
        import os
        os.unlink(tmp_file_path)

@router.post("/execute", response_model=ImportExecuteResponse)
async def execute_import(
    template_id: UUID = Form(...),
    company_id: UUID = Form(...),
    user_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Execute import and save to database"""
    
    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        contents = await file.read()
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name
    
    try:
        import_engine = ImportEngine(db)
        
        # Run actual import
        result = await import_engine.process_import(
            template_id=str(template_id),
            company_id=str(company_id),
            file_path=tmp_file_path,
            user_id=str(user_id),
            dry_run=False
        )
        
        return ImportExecuteResponse(
            job_id=result['job_id'],
            status=result['status'],
            total_records=result['total_records'],
            successful_records=result['successful_records'],
            failed_records=result['failed_records'],
            skipped_records=result['skipped_records'],
            errors=result.get('errors', []),
            warnings=result.get('warnings', [])
        )
        
    finally:
        # Clean up temporary file
        import os
        os.unlink(tmp_file_path)

# ============================================
# IMPORT JOBS
# ============================================

@router.get("/jobs", response_model=List[ImportJobResponse])
async def list_import_jobs(
    company_id: UUID,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List import jobs for a company"""
    
    query = """
    SELECT 
        ij.*,
        it.name as template_name,
        u.email as executed_by_email
    FROM import_jobs ij
    LEFT JOIN import_templates it ON it.id = ij.template_id
    LEFT JOIN users u ON u.id = ij.executed_by
    WHERE ij.company_id = :company_id
    """
    
    params = {'company_id': company_id}
    
    if status:
        query += " AND ij.status = :status"
        params['status'] = status
    
    query += " ORDER BY ij.created_at DESC LIMIT :limit"
    params['limit'] = limit
    
    result = db.execute(query, params)
    return [dict(row) for row in result.fetchall()]

@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Get details of a specific import job"""
    
    query = """
    SELECT 
        ij.*,
        it.name as template_name,
        u.email as executed_by_email
    FROM import_jobs ij
    LEFT JOIN import_templates it ON it.id = ij.template_id
    LEFT JOIN users u ON u.id = ij.executed_by
    WHERE ij.id = :job_id
    """
    
    result = db.execute(query, {'job_id': job_id})
    job = result.fetchone()
    
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    return dict(job)

@router.get("/jobs/{job_id}/details")
async def get_import_job_details(
    job_id: UUID,
    status_filter: Optional[str] = None,
    limit: int = Query(100, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Get row-level details of an import job"""
    
    query = """
    SELECT * FROM import_job_details
    WHERE import_job_id = :job_id
    """
    
    params = {'job_id': job_id}
    
    if status_filter:
        query += " AND status = :status"
        params['status'] = status_filter
    
    query += " ORDER BY row_number LIMIT :limit"
    params['limit'] = limit
    
    result = db.execute(query, params)
    return [dict(row) for row in result.fetchall()]

@router.get("/jobs/{job_id}/errors/export")
async def export_import_errors(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """Export import job errors as CSV"""
    
    query = """
    SELECT 
        row_number,
        source_data,
        error_message,
        created_at
    FROM import_job_details
    WHERE import_job_id = :job_id
    AND status = 'failed'
    ORDER BY row_number
    """
    
    result = db.execute(query, {'job_id': job_id})
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Row Number', 'Source Data', 'Error Message', 'Timestamp'])
    
    # Write data
    for row in result:
        writer.writerow([
            row['row_number'],
            json.dumps(row['source_data']),
            row['error_message'],
            row['created_at']
        ])
    
    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=import_errors_{job_id}.csv"
        }
    )

# ============================================
# UNMAPPED CODES
# ============================================

@router.post("/unmapped-codes")
async def check_unmapped_codes(
    company_id: UUID = Form(...),
    lookup_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Check which codes in a file don't have mappings"""
    
    # Read file and extract codes
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # Assume first column contains the codes
    codes = df.iloc[:, 0].unique().tolist()
    
    mapping_service = MappingService(db)
    unmapped = await mapping_service.get_unmapped_codes(
        str(company_id),
        lookup_type,
        [str(code) for code in codes]
    )
    
    return {
        'total_codes': len(codes),
        'unmapped_count': len(unmapped),
        'unmapped_codes': unmapped
    }