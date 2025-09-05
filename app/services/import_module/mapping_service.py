from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import re
from datetime import datetime

class MappingService:
    """
    Service for handling field mappings and data lookups during import
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.lookup_cache = {}
        
    async def load_field_mappings(self, template_id: str) -> List[Dict[str, Any]]:
        """Load field mappings for a template"""
        query = """
        SELECT * FROM field_mappings
        WHERE template_id = :template_id
        ORDER BY field_order
        """
        
        result = self.db.execute(text(query), {'template_id': template_id})
        mappings = [dict(row._mapping) for row in result.fetchall()]
        
        return mappings
    
    async def map_to_internal(
        self,
        data: Dict[str, Any],
        field_mappings: List[Dict[str, Any]],
        company_id: str
    ) -> Dict[str, Any]:
        """Map transformed data to internal structure"""
        
        mapped_data = {'company_id': company_id}
        
        for mapping in field_mappings:
            source_field = mapping['source_field']
            target_field = mapping['target_field']
            transformation_type = mapping['transformation_type']
            
            if source_field not in data and mapping.get('is_required'):
                raise ValueError(f"Required field {source_field} not found in data")
            
            value = data.get(source_field)
            
            # Apply mapping transformation
            if transformation_type == 'lookup':
                value = await self._apply_lookup(
                    value,
                    mapping.get('transformation_config', {}),
                    company_id
                )
            elif transformation_type == 'concatenate':
                value = await self._apply_concatenation(
                    data,
                    mapping.get('transformation_config', {})
                )
            elif transformation_type == 'split':
                value = await self._apply_split(
                    value,
                    mapping.get('transformation_config', {})
                )
            
            # Handle nested fields (e.g., "lines.gl_account_id")
            if '.' in target_field:
                self._set_nested_value(mapped_data, target_field, value)
            else:
                mapped_data[target_field] = value
        
        return mapped_data
    
    async def _apply_lookup(
        self,
        value: Any,
        config: Dict[str, Any],
        company_id: str
    ) -> Any:
        """Apply lookup transformation to map external codes to internal IDs"""
        
        if value is None:
            return None
        
        lookup_type = config.get('lookup_type')
        cache_key = f"{company_id}:{lookup_type}:{value}"
        
        # Check cache first
        if cache_key in self.lookup_cache:
            return self.lookup_cache[cache_key]
        
        # Perform lookup based on type
        if lookup_type == 'account':
            result = await self._lookup_account(value, company_id)
        elif lookup_type == 'cost_center':
            result = await self._lookup_cost_center(value, company_id)
        elif lookup_type == 'fiscal_period':
            result = await self._lookup_fiscal_period(value, company_id)
        elif lookup_type == 'custom':
            result = await self._lookup_custom(value, company_id, config)
        else:
            # Try mapping_lookups table
            result = await self._lookup_mapping_table(value, company_id, lookup_type)
        
        # Cache the result
        self.lookup_cache[cache_key] = result
        return result
    
    async def _lookup_account(self, account_code: str, company_id: str) -> Optional[str]:
        """Lookup GL account by code"""
        query = """
        SELECT id FROM gl_accounts
        WHERE company_id = :company_id
        AND account_number = :account_code
        AND is_active = true
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'account_code': account_code
        })
        
        row = result.fetchone()
        return str(row[0]) if row else None
    
    async def _lookup_cost_center(self, cost_center_code: str, company_id: str) -> Optional[str]:
        """Lookup cost center by code"""
        query = """
        SELECT id FROM cost_centers
        WHERE company_id = :company_id
        AND code = :cost_center_code
        AND is_active = true
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'cost_center_code': cost_center_code
        })
        
        row = result.fetchone()
        return str(row[0]) if row else None
    
    async def _lookup_fiscal_period(self, period_identifier: str, company_id: str) -> Optional[str]:
        """Lookup fiscal period by identifier (e.g., "2024-01" or "202401")"""
        
        # Try different date formats
        if '-' in period_identifier:
            parts = period_identifier.split('-')
            if len(parts) == 2:
                year = int(parts[0])
                period = int(parts[1])
            else:
                return None
        elif len(period_identifier) == 6:
            year = int(period_identifier[:4])
            period = int(period_identifier[4:])
        else:
            return None
        
        query = """
        SELECT id FROM fiscal_periods
        WHERE company_id = :company_id
        AND fiscal_year = :year
        AND period_number = :period
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'year': year,
            'period': period
        })
        
        row = result.fetchone()
        return str(row[0]) if row else None
    
    async def _lookup_mapping_table(
        self,
        external_code: str,
        company_id: str,
        lookup_type: str
    ) -> Optional[str]:
        """Lookup from mapping_lookups table"""
        query = """
        SELECT internal_id FROM mapping_lookups
        WHERE company_id = :company_id
        AND lookup_type = :lookup_type
        AND external_code = :external_code
        AND is_active = true
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'lookup_type': lookup_type,
            'external_code': external_code
        })
        
        row = result.fetchone()
        return str(row[0]) if row else None
    
    async def _lookup_custom(
        self,
        value: str,
        company_id: str,
        config: Dict[str, Any]
    ) -> Any:
        """Apply custom lookup based on configuration"""
        
        table_name = config.get('table')
        match_field = config.get('match_field')
        return_field = config.get('return_field', 'id')
        additional_filters = config.get('filters', {})
        
        # Build dynamic query
        conditions = [f"{match_field} = :match_value"]
        params = {'match_value': value}
        
        if 'company_id' in additional_filters:
            conditions.append("company_id = :company_id")
            params['company_id'] = company_id
        
        for field, field_value in additional_filters.items():
            if field != 'company_id':
                conditions.append(f"{field} = :{field}")
                params[field] = field_value
        
        where_clause = " AND ".join(conditions)
        query = f"SELECT {return_field} FROM {table_name} WHERE {where_clause}"
        
        result = self.db.execute(text(query), params)
        row = result.fetchone()
        
        return row[0] if row else None
    
    async def _apply_concatenation(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Concatenate multiple fields"""
        
        fields = config.get('fields', [])
        separator = config.get('separator', '')
        
        values = []
        for field in fields:
            value = data.get(field, '')
            if value:
                values.append(str(value))
        
        return separator.join(values)
    
    async def _apply_split(
        self,
        value: str,
        config: Dict[str, Any]
    ) -> Any:
        """Split a field value"""
        
        if not value:
            return None
        
        delimiter = config.get('delimiter', ',')
        index = config.get('index', 0)
        
        parts = str(value).split(delimiter)
        
        if index < len(parts):
            return parts[index].strip()
        
        return None
    
    def _set_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
        value: Any
    ):
        """Set a value in a nested dictionary structure"""
        
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            # Handle array notation (e.g., "lines[0]")
            if '[' in key:
                base_key = key[:key.index('[')]
                index = int(key[key.index('[') + 1:key.index(']')])
                
                if base_key not in current:
                    current[base_key] = []
                
                while len(current[base_key]) <= index:
                    current[base_key].append({})
                
                current = current[base_key][index]
            else:
                if key not in current:
                    current[key] = {}
                current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        if '[' in final_key:
            base_key = final_key[:final_key.index('[')]
            index = int(final_key[final_key.index('[') + 1:final_key.index(']')])
            
            if base_key not in current:
                current[base_key] = []
            
            while len(current[base_key]) <= index:
                current[base_key].append(None)
            
            current[base_key][index] = value
        else:
            current[final_key] = value
    
    async def create_mapping_lookup(
        self,
        company_id: str,
        lookup_type: str,
        external_code: str,
        internal_id: str,
        description: Optional[str] = None
    ) -> str:
        """Create a new mapping lookup entry"""
        
        import uuid
        lookup_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO mapping_lookups (
            id, company_id, lookup_type, external_code,
            internal_id, description, is_active, created_at
        ) VALUES (
            :id, :company_id, :lookup_type, :external_code,
            :internal_id, :description, true, :created_at
        )
        ON CONFLICT (company_id, lookup_type, external_code)
        DO UPDATE SET
            internal_id = EXCLUDED.internal_id,
            description = EXCLUDED.description,
            updated_at = EXCLUDED.created_at
        RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': lookup_id,
            'company_id': company_id,
            'lookup_type': lookup_type,
            'external_code': external_code,
            'internal_id': internal_id,
            'description': description,
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        
        # Clear cache for this lookup
        cache_key = f"{company_id}:{lookup_type}:{external_code}"
        if cache_key in self.lookup_cache:
            del self.lookup_cache[cache_key]
        
        return result.fetchone()[0]
    
    async def get_unmapped_codes(
        self,
        company_id: str,
        lookup_type: str,
        external_codes: List[str]
    ) -> List[str]:
        """Get list of external codes that don't have mappings"""
        
        if not external_codes:
            return []
        
        query = """
        SELECT external_code FROM mapping_lookups
        WHERE company_id = :company_id
        AND lookup_type = :lookup_type
        AND external_code = ANY(:codes)
        AND is_active = true
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'lookup_type': lookup_type,
            'codes': external_codes
        })
        
        mapped_codes = {row[0] for row in result.fetchall()}
        unmapped = [code for code in external_codes if code not in mapped_codes]
        
        return unmapped