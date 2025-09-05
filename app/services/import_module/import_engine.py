from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import json
import uuid
from pathlib import Path
import asyncio
from enum import Enum

from .mapping_service import MappingService
from .validation_service import ValidationService
from .transformation_service import TransformationService
from ...models.models import Company, GLAccount, CostCenter, FiscalPeriod

class ImportStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class SourceType(Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    API = "api"
    DATABASE = "database"

class ImportEngine:
    """
    Core engine for handling data imports with validation, transformation, and mapping
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapping_service = MappingService(db)
        self.validation_service = ValidationService(db)
        self.transformation_service = TransformationService(db)
        self.import_job_id = None
        self.errors = []
        self.warnings = []
        
    async def create_import_job(
        self,
        template_id: str,
        company_id: str,
        source_file_path: str,
        user_id: str
    ) -> str:
        """Create a new import job record"""
        job_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO import_jobs (
            id, template_id, company_id, status, source_file_path,
            executed_by, created_at
        ) VALUES (
            :job_id, :template_id, :company_id, :status, :source_file_path,
            :user_id, :created_at
        )
        """
        
        self.db.execute(text(query), {
            'job_id': job_id,
            'template_id': template_id,
            'company_id': company_id,
            'status': ImportStatus.PENDING.value,
            'source_file_path': source_file_path,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        })
        self.db.commit()
        
        self.import_job_id = job_id
        return job_id
    
    async def load_template(self, template_id: str) -> Dict[str, Any]:
        """Load import template configuration"""
        query = """
        SELECT * FROM import_templates WHERE id = :template_id
        """
        result = self.db.execute(text(query), {'template_id': template_id})
        template = result.fetchone()
        
        if not template:
            raise ValueError(f"Import template {template_id} not found")
        
        return dict(template._mapping)
    
    async def parse_source_file(
        self,
        file_path: str,
        source_type: str,
        file_format: Dict[str, Any]
    ) -> pd.DataFrame:
        """Parse source file based on type and format configuration"""
        
        if source_type == SourceType.CSV.value:
            delimiter = file_format.get('delimiter', ',')
            encoding = file_format.get('encoding', 'utf-8')
            header_row = file_format.get('header_row', 0)
            
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                encoding=encoding,
                header=header_row
            )
            
        elif source_type == SourceType.EXCEL.value:
            sheet_name = file_format.get('sheet_name', 0)
            header_row = file_format.get('header_row', 0)
            
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header_row
            )
            
        elif source_type == SourceType.JSON.value:
            with open(file_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return df
    
    async def process_import(
        self,
        template_id: str,
        company_id: str,
        file_path: str,
        user_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Main import processing method
        """
        
        # Create import job
        if not dry_run:
            job_id = await self.create_import_job(
                template_id, company_id, file_path, user_id
            )
        
        try:
            # Update status to validating
            await self._update_job_status(ImportStatus.VALIDATING)
            
            # Load template
            template = await self.load_template(template_id)
            
            # Parse source file
            df = await self.parse_source_file(
                file_path,
                template['source_type'],
                json.loads(template['file_format']) if template['file_format'] else {}
            )
            
            total_records = len(df)
            await self._update_job_record_count(total_records)
            
            # Load field mappings
            field_mappings = await self.mapping_service.load_field_mappings(template_id)
            
            # Process each row
            successful_records = 0
            failed_records = 0
            skipped_records = 0
            processed_data = []
            
            await self._update_job_status(ImportStatus.PROCESSING)
            
            for index, row in df.iterrows():
                try:
                    # Validate row
                    validation_result = await self.validation_service.validate_row(
                        row.to_dict(),
                        template.get('validation_rules', {}),
                        field_mappings
                    )
                    
                    if not validation_result['is_valid']:
                        if validation_result['severity'] == 'error':
                            failed_records += 1
                            await self._log_row_error(
                                index + 1,
                                row.to_dict(),
                                validation_result['errors']
                            )
                            continue
                        else:
                            # Log warning but continue
                            self.warnings.extend(validation_result['warnings'])
                    
                    # Transform data
                    transformed_data = await self.transformation_service.transform_row(
                        row.to_dict(),
                        field_mappings,
                        template.get('transformation_rules', {})
                    )
                    
                    # Map to internal structure
                    mapped_data = await self.mapping_service.map_to_internal(
                        transformed_data,
                        field_mappings,
                        company_id
                    )
                    
                    if dry_run:
                        processed_data.append(mapped_data)
                    else:
                        # Import to database
                        entity_id = await self._import_to_database(
                            mapped_data,
                            template['target_entity']
                        )
                        
                        # Log successful import
                        await self._log_row_success(
                            index + 1,
                            row.to_dict(),
                            transformed_data,
                            entity_id,
                            template['target_entity']
                        )
                    
                    successful_records += 1
                    
                except Exception as e:
                    failed_records += 1
                    await self._log_row_error(
                        index + 1,
                        row.to_dict(),
                        str(e)
                    )
                    
                # Update progress periodically
                if (index + 1) % 100 == 0:
                    await self._update_job_progress(
                        index + 1,
                        successful_records,
                        failed_records,
                        skipped_records
                    )
            
            # Final status update
            if failed_records == 0:
                await self._update_job_status(ImportStatus.COMPLETED)
            elif successful_records > 0:
                await self._update_job_status(ImportStatus.PARTIAL)
            else:
                await self._update_job_status(ImportStatus.FAILED)
            
            # Update final counts
            await self._update_job_progress(
                total_records,
                successful_records,
                failed_records,
                skipped_records
            )
            
            return {
                'job_id': self.import_job_id if not dry_run else None,
                'status': 'completed' if failed_records == 0 else 'partial',
                'total_records': total_records,
                'successful_records': successful_records,
                'failed_records': failed_records,
                'skipped_records': skipped_records,
                'errors': self.errors,
                'warnings': self.warnings,
                'preview_data': processed_data[:10] if dry_run else None
            }
            
        except Exception as e:
            await self._update_job_status(ImportStatus.FAILED)
            await self._log_job_error(str(e))
            raise
    
    async def _import_to_database(
        self,
        data: Dict[str, Any],
        target_entity: str
    ) -> str:
        """Import mapped data to the appropriate database table"""
        
        if target_entity == 'gl_transactions':
            return await self._import_gl_transaction(data)
        elif target_entity == 'budget_lines':
            return await self._import_budget_line(data)
        elif target_entity == 'kpis':
            return await self._import_kpi(data)
        else:
            raise ValueError(f"Unsupported target entity: {target_entity}")
    
    async def _import_gl_transaction(self, data: Dict[str, Any]) -> str:
        """Import GL transaction with lines"""
        transaction_id = str(uuid.uuid4())
        
        # Create main transaction
        query = """
        INSERT INTO gl_transactions (
            id, company_id, transaction_date, fiscal_period_id,
            reference_number, description, source_system,
            external_id, is_posted, created_at
        ) VALUES (
            :id, :company_id, :transaction_date, :fiscal_period_id,
            :reference_number, :description, 'import',
            :external_id, false, :created_at
        )
        """
        
        self.db.execute(text(query), {
            'id': transaction_id,
            'company_id': data['company_id'],
            'transaction_date': data['transaction_date'],
            'fiscal_period_id': data.get('fiscal_period_id'),
            'reference_number': data.get('reference_number'),
            'description': data.get('description'),
            'external_id': data.get('external_id'),
            'created_at': datetime.utcnow()
        })
        
        # Create transaction lines
        for line in data.get('lines', []):
            line_id = str(uuid.uuid4())
            line_query = """
            INSERT INTO gl_transaction_lines (
                id, gl_transaction_id, gl_account_id, cost_center_id,
                debit_amount, credit_amount, description, created_at
            ) VALUES (
                :id, :transaction_id, :gl_account_id, :cost_center_id,
                :debit_amount, :credit_amount, :description, :created_at
            )
            """
            
            self.db.execute(text(line_query), {
                'id': line_id,
                'transaction_id': transaction_id,
                'gl_account_id': line['gl_account_id'],
                'cost_center_id': line.get('cost_center_id'),
                'debit_amount': line.get('debit_amount', 0),
                'credit_amount': line.get('credit_amount', 0),
                'description': line.get('description'),
                'created_at': datetime.utcnow()
            })
        
        self.db.commit()
        return transaction_id
    
    async def _import_budget_line(self, data: Dict[str, Any]) -> str:
        """Import budget line item"""
        budget_line_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO budget_lines (
            id, scenario_id, gl_account_id, cost_center_id,
            fiscal_period_id, amount, quantity, rate,
            notes, created_at
        ) VALUES (
            :id, :scenario_id, :gl_account_id, :cost_center_id,
            :fiscal_period_id, :amount, :quantity, :rate,
            :notes, :created_at
        )
        ON CONFLICT (scenario_id, gl_account_id, cost_center_id, fiscal_period_id)
        DO UPDATE SET
            amount = EXCLUDED.amount,
            quantity = EXCLUDED.quantity,
            rate = EXCLUDED.rate,
            notes = EXCLUDED.notes,
            updated_at = :created_at
        RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': budget_line_id,
            'scenario_id': data['scenario_id'],
            'gl_account_id': data['gl_account_id'],
            'cost_center_id': data.get('cost_center_id'),
            'fiscal_period_id': data['fiscal_period_id'],
            'amount': data['amount'],
            'quantity': data.get('quantity'),
            'rate': data.get('rate'),
            'notes': data.get('notes'),
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return result.fetchone()[0]
    
    async def _update_job_status(self, status: ImportStatus):
        """Update import job status"""
        if not self.import_job_id:
            return
        
        query = """
        UPDATE import_jobs
        SET status = :status,
            updated_at = :updated_at
        WHERE id = :job_id
        """
        
        self.db.execute(text(query), {
            'status': status.value,
            'updated_at': datetime.utcnow(),
            'job_id': self.import_job_id
        })
        self.db.commit()
    
    async def _update_job_record_count(self, total_records: int):
        """Update total record count for job"""
        if not self.import_job_id:
            return
        
        query = """
        UPDATE import_jobs
        SET total_records = :total_records,
            start_time = :start_time
        WHERE id = :job_id
        """
        
        self.db.execute(text(query), {
            'total_records': total_records,
            'start_time': datetime.utcnow(),
            'job_id': self.import_job_id
        })
        self.db.commit()
    
    async def _update_job_progress(
        self,
        processed: int,
        successful: int,
        failed: int,
        skipped: int
    ):
        """Update job progress counts"""
        if not self.import_job_id:
            return
        
        query = """
        UPDATE import_jobs
        SET processed_records = :processed,
            successful_records = :successful,
            failed_records = :failed,
            skipped_records = :skipped,
            updated_at = :updated_at
        WHERE id = :job_id
        """
        
        self.db.execute(text(query), {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'updated_at': datetime.utcnow(),
            'job_id': self.import_job_id
        })
        self.db.commit()
    
    async def _log_row_success(
        self,
        row_number: int,
        source_data: Dict,
        transformed_data: Dict,
        entity_id: str,
        entity_type: str
    ):
        """Log successful row import"""
        if not self.import_job_id:
            return
        
        detail_id = str(uuid.uuid4())
        query = """
        INSERT INTO import_job_details (
            id, import_job_id, row_number, source_data,
            transformed_data, status, created_entity_id,
            created_entity_type, created_at
        ) VALUES (
            :id, :job_id, :row_number, :source_data,
            :transformed_data, 'success', :entity_id,
            :entity_type, :created_at
        )
        """
        
        self.db.execute(text(query), {
            'id': detail_id,
            'job_id': self.import_job_id,
            'row_number': row_number,
            'source_data': json.dumps(source_data),
            'transformed_data': json.dumps(transformed_data),
            'entity_id': entity_id,
            'entity_type': entity_type,
            'created_at': datetime.utcnow()
        })
        self.db.commit()
    
    async def _log_row_error(
        self,
        row_number: int,
        source_data: Dict,
        error_message: str
    ):
        """Log row import error"""
        if not self.import_job_id:
            self.errors.append({
                'row': row_number,
                'error': error_message
            })
            return
        
        detail_id = str(uuid.uuid4())
        query = """
        INSERT INTO import_job_details (
            id, import_job_id, row_number, source_data,
            status, error_message, created_at
        ) VALUES (
            :id, :job_id, :row_number, :source_data,
            'failed', :error_message, :created_at
        )
        """
        
        self.db.execute(text(query), {
            'id': detail_id,
            'job_id': self.import_job_id,
            'row_number': row_number,
            'source_data': json.dumps(source_data),
            'error_message': error_message,
            'created_at': datetime.utcnow()
        })
        self.db.commit()
        
        self.errors.append({
            'row': row_number,
            'error': error_message
        })
    
    async def _log_job_error(self, error_message: str):
        """Log job-level error"""
        if not self.import_job_id:
            return
        
        query = """
        UPDATE import_jobs
        SET error_summary = :error_summary,
            end_time = :end_time
        WHERE id = :job_id
        """
        
        self.db.execute(text(query), {
            'error_summary': json.dumps({'error': error_message}),
            'end_time': datetime.utcnow(),
            'job_id': self.import_job_id
        })
        self.db.commit()