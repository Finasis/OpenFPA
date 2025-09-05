from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from datetime import datetime, date
from decimal import Decimal
import json

class TransformationService:
    """
    Service for transforming import data according to defined rules
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def transform_row(
        self,
        row_data: Dict[str, Any],
        field_mappings: List[Dict[str, Any]],
        transformation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform a row of data according to mapping and transformation rules"""
        
        transformed_data = {}
        
        # Apply field-level transformations from mappings
        for mapping in field_mappings:
            source_field = mapping['source_field']
            value = row_data.get(source_field)
            
            # Apply default value if field is missing
            if value is None or value == '':
                if mapping.get('default_value'):
                    value = mapping['default_value']
                elif mapping.get('is_required'):
                    continue  # Skip required fields without values
                else:
                    transformed_data[source_field] = None
                    continue
            
            # Apply transformation based on data type
            data_type = mapping.get('data_type')
            if data_type:
                value = await self._transform_by_type(value, data_type)
            
            # Apply transformation configuration
            transform_config = mapping.get('transformation_config', {})
            if transform_config:
                value = await self._apply_transformation_config(
                    value, transform_config, row_data
                )
            
            transformed_data[source_field] = value
        
        # Apply template-level transformation rules
        if transformation_rules:
            transformed_data = await self._apply_template_transformations(
                transformed_data, transformation_rules
            )
        
        return transformed_data
    
    async def _transform_by_type(self, value: Any, data_type: str) -> Any:
        """Transform value based on data type"""
        
        if value is None or value == '':
            return None
        
        try:
            if data_type == 'string':
                return str(value).strip()
            
            elif data_type == 'number':
                # Handle various number formats
                if isinstance(value, (int, float, Decimal)):
                    return float(value)
                
                # Clean string representations
                value_str = str(value).strip()
                # Remove currency symbols and thousands separators
                value_str = re.sub(r'[$,€£¥]', '', value_str)
                value_str = value_str.replace(',', '')
                
                # Handle percentages
                if value_str.endswith('%'):
                    return float(value_str[:-1]) / 100
                
                # Handle parentheses for negative numbers
                if value_str.startswith('(') and value_str.endswith(')'):
                    value_str = '-' + value_str[1:-1]
                
                return float(value_str)
            
            elif data_type == 'date':
                if isinstance(value, (date, datetime)):
                    return value
                
                # Try common date formats
                date_formats = [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y/%m/%d',
                    '%d-%m-%Y',
                    '%m-%d-%Y',
                    '%Y%m%d'
                ]
                
                value_str = str(value).strip()
                for fmt in date_formats:
                    try:
                        return datetime.strptime(value_str, fmt).date()
                    except ValueError:
                        continue
                
                # If no format matches, return as string
                return value_str
            
            elif data_type == 'boolean':
                if isinstance(value, bool):
                    return value
                
                value_str = str(value).lower().strip()
                return value_str in ['true', '1', 'yes', 'y', 'on']
            
            else:
                return value
                
        except Exception:
            # If transformation fails, return original value
            return value
    
    async def _apply_transformation_config(
        self,
        value: Any,
        config: Dict[str, Any],
        row_data: Dict[str, Any]
    ) -> Any:
        """Apply specific transformation configuration"""
        
        transform_type = config.get('type')
        
        if transform_type == 'uppercase':
            return str(value).upper() if value else value
        
        elif transform_type == 'lowercase':
            return str(value).lower() if value else value
        
        elif transform_type == 'trim':
            return str(value).strip() if value else value
        
        elif transform_type == 'replace':
            if value and config.get('find') and config.get('replace_with') is not None:
                return str(value).replace(
                    config['find'],
                    config['replace_with']
                )
            return value
        
        elif transform_type == 'regex_replace':
            if value and config.get('pattern') and config.get('replacement') is not None:
                return re.sub(
                    config['pattern'],
                    config['replacement'],
                    str(value)
                )
            return value
        
        elif transform_type == 'prefix':
            prefix = config.get('prefix', '')
            return f"{prefix}{value}" if value else value
        
        elif transform_type == 'suffix':
            suffix = config.get('suffix', '')
            return f"{value}{suffix}" if value else value
        
        elif transform_type == 'pad':
            if value:
                length = config.get('length', 10)
                char = config.get('char', '0')
                direction = config.get('direction', 'left')
                
                value_str = str(value)
                if direction == 'left':
                    return value_str.rjust(length, char)
                else:
                    return value_str.ljust(length, char)
            return value
        
        elif transform_type == 'extract':
            if value and config.get('pattern'):
                match = re.search(config['pattern'], str(value))
                if match:
                    group = config.get('group', 0)
                    return match.group(group)
            return value
        
        elif transform_type == 'calculate':
            return await self._apply_calculation(value, config, row_data)
        
        elif transform_type == 'map_values':
            # Map specific values to other values
            value_map = config.get('map', {})
            return value_map.get(str(value), value)
        
        elif transform_type == 'date_format':
            if value:
                input_format = config.get('input_format', '%Y-%m-%d')
                output_format = config.get('output_format', '%Y-%m-%d')
                
                try:
                    if isinstance(value, str):
                        dt = datetime.strptime(value, input_format)
                    elif isinstance(value, (date, datetime)):
                        dt = value
                    else:
                        return value
                    
                    if isinstance(dt, datetime):
                        return dt.strftime(output_format)
                    else:
                        return dt.strftime(output_format)
                except:
                    return value
            return value
        
        elif transform_type == 'conditional':
            return await self._apply_conditional(value, config, row_data)
        
        else:
            return value
    
    async def _apply_calculation(
        self,
        value: Any,
        config: Dict[str, Any],
        row_data: Dict[str, Any]
    ) -> Any:
        """Apply calculation transformation"""
        
        operation = config.get('operation')
        
        if operation == 'multiply':
            multiplier = config.get('multiplier', 1)
            if isinstance(multiplier, str) and multiplier in row_data:
                multiplier = self._to_numeric(row_data[multiplier])
            else:
                multiplier = self._to_numeric(multiplier)
            
            value_num = self._to_numeric(value)
            if value_num is not None and multiplier is not None:
                return value_num * multiplier
        
        elif operation == 'divide':
            divisor = config.get('divisor', 1)
            if isinstance(divisor, str) and divisor in row_data:
                divisor = self._to_numeric(row_data[divisor])
            else:
                divisor = self._to_numeric(divisor)
            
            value_num = self._to_numeric(value)
            if value_num is not None and divisor and divisor != 0:
                return value_num / divisor
        
        elif operation == 'add':
            addend = config.get('addend', 0)
            if isinstance(addend, str) and addend in row_data:
                addend = self._to_numeric(row_data[addend])
            else:
                addend = self._to_numeric(addend)
            
            value_num = self._to_numeric(value)
            if value_num is not None and addend is not None:
                return value_num + addend
        
        elif operation == 'subtract':
            subtrahend = config.get('subtrahend', 0)
            if isinstance(subtrahend, str) and subtrahend in row_data:
                subtrahend = self._to_numeric(row_data[subtrahend])
            else:
                subtrahend = self._to_numeric(subtrahend)
            
            value_num = self._to_numeric(value)
            if value_num is not None and subtrahend is not None:
                return value_num - subtrahend
        
        elif operation == 'percentage':
            base = config.get('base')
            if base and base in row_data:
                base_value = self._to_numeric(row_data[base])
                value_num = self._to_numeric(value)
                if base_value and value_num is not None:
                    return (value_num / base_value) * 100
        
        elif operation == 'round':
            decimals = config.get('decimals', 2)
            value_num = self._to_numeric(value)
            if value_num is not None:
                return round(value_num, decimals)
        
        return value
    
    async def _apply_conditional(
        self,
        value: Any,
        config: Dict[str, Any],
        row_data: Dict[str, Any]
    ) -> Any:
        """Apply conditional transformation"""
        
        conditions = config.get('conditions', [])
        
        for condition in conditions:
            if await self._evaluate_condition(condition, value, row_data):
                return condition.get('then_value', value)
        
        # Return default value if no condition matches
        return config.get('else_value', value)
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        value: Any,
        row_data: Dict[str, Any]
    ) -> bool:
        """Evaluate a conditional expression"""
        
        condition_type = condition.get('type')
        
        if condition_type == 'equals':
            compare_to = condition.get('value')
            if isinstance(compare_to, str) and compare_to.startswith('$'):
                # Reference to another field
                field_name = compare_to[1:]
                compare_to = row_data.get(field_name)
            return value == compare_to
        
        elif condition_type == 'not_equals':
            compare_to = condition.get('value')
            if isinstance(compare_to, str) and compare_to.startswith('$'):
                field_name = compare_to[1:]
                compare_to = row_data.get(field_name)
            return value != compare_to
        
        elif condition_type == 'contains':
            search_str = condition.get('value', '')
            return search_str in str(value) if value else False
        
        elif condition_type == 'starts_with':
            prefix = condition.get('value', '')
            return str(value).startswith(prefix) if value else False
        
        elif condition_type == 'ends_with':
            suffix = condition.get('value', '')
            return str(value).endswith(suffix) if value else False
        
        elif condition_type == 'is_empty':
            return value is None or value == ''
        
        elif condition_type == 'is_not_empty':
            return value is not None and value != ''
        
        elif condition_type == 'greater_than':
            threshold = self._to_numeric(condition.get('value'))
            value_num = self._to_numeric(value)
            if threshold is not None and value_num is not None:
                return value_num > threshold
        
        elif condition_type == 'less_than':
            threshold = self._to_numeric(condition.get('value'))
            value_num = self._to_numeric(value)
            if threshold is not None and value_num is not None:
                return value_num < threshold
        
        elif condition_type == 'between':
            min_val = self._to_numeric(condition.get('min'))
            max_val = self._to_numeric(condition.get('max'))
            value_num = self._to_numeric(value)
            if all(v is not None for v in [min_val, max_val, value_num]):
                return min_val <= value_num <= max_val
        
        elif condition_type == 'in_list':
            values_list = condition.get('values', [])
            return value in values_list
        
        elif condition_type == 'regex':
            pattern = condition.get('pattern')
            if pattern:
                return bool(re.match(pattern, str(value))) if value else False
        
        return False
    
    async def _apply_template_transformations(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply template-level transformations"""
        
        # Apply derived fields
        if 'derived_fields' in rules:
            for field_config in rules['derived_fields']:
                field_name = field_config.get('name')
                if field_name:
                    data[field_name] = await self._calculate_derived_field(
                        data, field_config
                    )
        
        # Apply global transformations
        if 'global_transforms' in rules:
            for transform in rules['global_transforms']:
                data = await self._apply_global_transform(data, transform)
        
        return data
    
    async def _calculate_derived_field(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Any:
        """Calculate a derived field value"""
        
        field_type = config.get('type')
        
        if field_type == 'concatenate':
            fields = config.get('fields', [])
            separator = config.get('separator', '')
            values = [str(data.get(f, '')) for f in fields]
            return separator.join(v for v in values if v)
        
        elif field_type == 'sum':
            fields = config.get('fields', [])
            total = 0
            for field in fields:
                value = self._to_numeric(data.get(field))
                if value is not None:
                    total += value
            return total
        
        elif field_type == 'difference':
            minuend = self._to_numeric(data.get(config.get('minuend')))
            subtrahend = self._to_numeric(data.get(config.get('subtrahend')))
            if minuend is not None and subtrahend is not None:
                return minuend - subtrahend
        
        elif field_type == 'product':
            fields = config.get('fields', [])
            result = 1
            for field in fields:
                value = self._to_numeric(data.get(field))
                if value is not None:
                    result *= value
                else:
                    return None
            return result
        
        elif field_type == 'lookup':
            # This would perform a database lookup
            # Implementation would depend on specific requirements
            pass
        
        elif field_type == 'constant':
            return config.get('value')
        
        elif field_type == 'current_date':
            return datetime.now().date()
        
        elif field_type == 'current_timestamp':
            return datetime.now()
        
        return None
    
    async def _apply_global_transform(
        self,
        data: Dict[str, Any],
        transform: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a global transformation to all data"""
        
        transform_type = transform.get('type')
        
        if transform_type == 'remove_empty':
            # Remove fields with empty values
            return {k: v for k, v in data.items() if v is not None and v != ''}
        
        elif transform_type == 'trim_all':
            # Trim all string values
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()
        
        elif transform_type == 'uppercase_all':
            # Convert all string values to uppercase
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.upper()
        
        elif transform_type == 'clean_numbers':
            # Clean all numeric fields
            for key, value in data.items():
                if isinstance(value, str) and any(c.isdigit() for c in value):
                    cleaned = self._to_numeric(value)
                    if cleaned is not None:
                        data[key] = cleaned
        
        return data
    
    def _to_numeric(self, value: Any) -> Optional[float]:
        """Convert value to numeric type"""
        
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        
        try:
            # Clean common number formats
            value_str = str(value).strip()
            value_str = re.sub(r'[$,€£¥]', '', value_str)
            value_str = value_str.replace(',', '')
            
            # Handle percentages
            if value_str.endswith('%'):
                return float(value_str[:-1]) / 100
            
            # Handle parentheses for negative
            if value_str.startswith('(') and value_str.endswith(')'):
                value_str = '-' + value_str[1:-1]
            
            return float(value_str)
        except (ValueError, TypeError):
            return None