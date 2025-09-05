from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import json

class ValidationService:
    """
    Service for validating import data against defined rules
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_errors = []
        self.validation_warnings = []
        
    async def validate_row(
        self,
        row_data: Dict[str, Any],
        validation_rules: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate a single row of data"""
        
        self.validation_errors = []
        self.validation_warnings = []
        
        # Apply field-level validations from mappings
        for mapping in field_mappings:
            field_name = mapping['source_field']
            field_value = row_data.get(field_name)
            
            # Check required fields
            if mapping.get('is_required') and (field_value is None or field_value == ''):
                self.validation_errors.append(
                    f"Required field '{field_name}' is missing or empty"
                )
                continue
            
            # Skip validation if field is optional and empty
            if field_value is None or field_value == '':
                continue
            
            # Validate data type
            expected_type = mapping.get('data_type')
            if expected_type:
                type_valid = await self._validate_data_type(
                    field_value, expected_type, field_name
                )
                if not type_valid:
                    continue
            
            # Apply regex validation
            validation_regex = mapping.get('validation_regex')
            if validation_regex:
                if not re.match(validation_regex, str(field_value)):
                    self.validation_errors.append(
                        f"Field '{field_name}' value '{field_value}' does not match pattern '{validation_regex}'"
                    )
        
        # Apply template-level validation rules
        if validation_rules:
            await self._apply_template_rules(row_data, validation_rules)
        
        # Determine overall validation result
        is_valid = len(self.validation_errors) == 0
        severity = 'error' if self.validation_errors else 'warning' if self.validation_warnings else 'info'
        
        return {
            'is_valid': is_valid,
            'severity': severity,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings
        }
    
    async def _validate_data_type(
        self,
        value: Any,
        expected_type: str,
        field_name: str
    ) -> bool:
        """Validate that a value matches the expected data type"""
        
        try:
            if expected_type == 'string':
                # Everything can be converted to string
                return True
            
            elif expected_type == 'number':
                # Try to convert to Decimal
                if isinstance(value, (int, float)):
                    return True
                try:
                    Decimal(str(value).replace(',', ''))
                    return True
                except (InvalidOperation, ValueError):
                    self.validation_errors.append(
                        f"Field '{field_name}' value '{value}' is not a valid number"
                    )
                    return False
            
            elif expected_type == 'date':
                # Try common date formats
                if isinstance(value, (date, datetime)):
                    return True
                
                date_formats = [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y/%m/%d',
                    '%d-%m-%Y',
                    '%m-%d-%Y'
                ]
                
                value_str = str(value)
                for fmt in date_formats:
                    try:
                        datetime.strptime(value_str, fmt)
                        return True
                    except ValueError:
                        continue
                
                self.validation_errors.append(
                    f"Field '{field_name}' value '{value}' is not a valid date"
                )
                return False
            
            elif expected_type == 'boolean':
                # Accept various boolean representations
                if isinstance(value, bool):
                    return True
                
                value_str = str(value).lower()
                if value_str in ['true', 'false', '1', '0', 'yes', 'no', 'y', 'n']:
                    return True
                
                self.validation_errors.append(
                    f"Field '{field_name}' value '{value}' is not a valid boolean"
                )
                return False
            
            else:
                # Unknown type, skip validation
                return True
                
        except Exception as e:
            self.validation_errors.append(
                f"Error validating field '{field_name}': {str(e)}"
            )
            return False
    
    async def _apply_template_rules(
        self,
        row_data: Dict[str, Any],
        rules: Dict[str, Any]
    ):
        """Apply template-level validation rules"""
        
        # Business logic validations
        if 'business_rules' in rules:
            for rule in rules['business_rules']:
                await self._apply_business_rule(row_data, rule)
        
        # Cross-field validations
        if 'cross_field_rules' in rules:
            for rule in rules['cross_field_rules']:
                await self._apply_cross_field_rule(row_data, rule)
        
        # Range validations
        if 'range_rules' in rules:
            for rule in rules['range_rules']:
                await self._apply_range_rule(row_data, rule)
    
    async def _apply_business_rule(
        self,
        row_data: Dict[str, Any],
        rule: Dict[str, Any]
    ):
        """Apply business logic validation rule"""
        
        rule_type = rule.get('type')
        
        if rule_type == 'balance_check':
            # Check if debits equal credits
            debit = self._get_numeric_value(row_data.get(rule.get('debit_field', 'debit_amount')))
            credit = self._get_numeric_value(row_data.get(rule.get('credit_field', 'credit_amount')))
            
            if debit is not None and credit is not None:
                if debit > 0 and credit > 0:
                    self.validation_errors.append(
                        "Both debit and credit amounts cannot be positive"
                    )
                elif abs(debit - credit) > 0.01 and rule.get('must_balance'):
                    self.validation_errors.append(
                        f"Debits ({debit}) do not equal credits ({credit})"
                    )
        
        elif rule_type == 'account_type_check':
            # Validate account type restrictions
            account_field = rule.get('account_field', 'account_code')
            account_code = row_data.get(account_field)
            
            if account_code:
                # This would need to lookup the account type
                # For now, just check prefix rules if provided
                type_prefixes = rule.get('type_prefixes', {})
                for account_type, prefixes in type_prefixes.items():
                    if any(str(account_code).startswith(p) for p in prefixes):
                        # Apply type-specific rules
                        if account_type == 'revenue' and rule.get('revenue_must_be_credit'):
                            debit = self._get_numeric_value(row_data.get('debit_amount'))
                            if debit and debit > 0:
                                self.validation_warnings.append(
                                    f"Revenue account {account_code} typically should have credit amounts"
                                )
        
        elif rule_type == 'custom':
            # Execute custom validation logic
            expression = rule.get('expression')
            if expression:
                try:
                    # Safe evaluation with limited scope
                    result = self._evaluate_expression(expression, row_data)
                    if not result:
                        message = rule.get('message', 'Custom validation failed')
                        severity = rule.get('severity', 'error')
                        
                        if severity == 'error':
                            self.validation_errors.append(message)
                        else:
                            self.validation_warnings.append(message)
                except Exception as e:
                    self.validation_warnings.append(
                        f"Could not evaluate custom rule: {str(e)}"
                    )
    
    async def _apply_cross_field_rule(
        self,
        row_data: Dict[str, Any],
        rule: Dict[str, Any]
    ):
        """Apply cross-field validation rule"""
        
        field1 = rule.get('field1')
        field2 = rule.get('field2')
        operator = rule.get('operator')
        
        if not all([field1, field2, operator]):
            return
        
        value1 = row_data.get(field1)
        value2 = row_data.get(field2)
        
        if value1 is None or value2 is None:
            return
        
        # Convert to appropriate types for comparison
        if rule.get('numeric_comparison'):
            value1 = self._get_numeric_value(value1)
            value2 = self._get_numeric_value(value2)
            
            if value1 is None or value2 is None:
                return
        
        # Apply operator
        valid = False
        if operator == 'equals':
            valid = value1 == value2
        elif operator == 'not_equals':
            valid = value1 != value2
        elif operator == 'greater_than':
            valid = value1 > value2
        elif operator == 'less_than':
            valid = value1 < value2
        elif operator == 'greater_or_equal':
            valid = value1 >= value2
        elif operator == 'less_or_equal':
            valid = value1 <= value2
        
        if not valid:
            message = rule.get('message', f"Cross-field validation failed: {field1} {operator} {field2}")
            severity = rule.get('severity', 'error')
            
            if severity == 'error':
                self.validation_errors.append(message)
            else:
                self.validation_warnings.append(message)
    
    async def _apply_range_rule(
        self,
        row_data: Dict[str, Any],
        rule: Dict[str, Any]
    ):
        """Apply range validation rule"""
        
        field = rule.get('field')
        min_value = rule.get('min')
        max_value = rule.get('max')
        
        if not field:
            return
        
        value = row_data.get(field)
        if value is None:
            return
        
        # Convert to numeric for comparison
        numeric_value = self._get_numeric_value(value)
        if numeric_value is None:
            return
        
        if min_value is not None and numeric_value < min_value:
            self.validation_errors.append(
                f"Field '{field}' value {numeric_value} is below minimum {min_value}"
            )
        
        if max_value is not None and numeric_value > max_value:
            self.validation_errors.append(
                f"Field '{field}' value {numeric_value} is above maximum {max_value}"
            )
    
    def _get_numeric_value(self, value: Any) -> Optional[float]:
        """Convert a value to numeric format"""
        
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        try:
            # Remove common formatting characters
            cleaned = str(value).replace(',', '').replace('$', '').replace('%', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _evaluate_expression(
        self,
        expression: str,
        context: Dict[str, Any]
    ) -> bool:
        """Safely evaluate a validation expression"""
        
        # Create a safe evaluation context
        safe_context = {
            'row': context,
            'len': len,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'all': all,
            'any': any,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool
        }
        
        # Replace field references with actual values
        for field, value in context.items():
            # Replace both row['field'] and row.field notations
            expression = expression.replace(f"row['{field}']", repr(value))
            expression = expression.replace(f'row["{field}"]', repr(value))
            expression = expression.replace(f"row.{field}", repr(value))
        
        # Evaluate the expression
        try:
            result = eval(expression, {"__builtins__": {}}, safe_context)
            return bool(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    async def validate_import_template(
        self,
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate an import template configuration"""
        
        errors = []
        warnings = []
        
        # Check required template fields
        required_fields = ['name', 'source_type', 'target_entity']
        for field in required_fields:
            if field not in template or not template[field]:
                errors.append(f"Template missing required field: {field}")
        
        # Validate source type
        valid_source_types = ['csv', 'excel', 'json', 'api', 'database']
        if template.get('source_type') not in valid_source_types:
            errors.append(f"Invalid source type: {template.get('source_type')}")
        
        # Validate target entity
        valid_targets = ['gl_transactions', 'budget_lines', 'kpis', 'gl_accounts', 'cost_centers']
        if template.get('target_entity') not in valid_targets:
            errors.append(f"Invalid target entity: {template.get('target_entity')}")
        
        # Validate file format configuration
        if template.get('source_type') == 'csv':
            file_format = template.get('file_format', {})
            if not file_format.get('delimiter'):
                warnings.append("CSV format missing delimiter, will use comma as default")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }