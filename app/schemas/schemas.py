from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pydantic.functional_validators import BeforeValidator
from pydantic.json_schema import JsonSchemaValue
from typing import Optional, List, Annotated, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from enum import Enum
import re

# Pydantic v2 configuration for better JSON handling
class BaseSchema(BaseModel):
    """Base schema with common configuration for all models"""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,  # Automatically strip whitespace from strings
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v),
        }
    )

class AccountTypeEnum(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class AccountSubtypeEnum(str, Enum):
    OPERATING = "operating"
    NON_OPERATING = "non_operating"
    CAPITAL = "capital"
    OTHER = "other"

class ScenarioTypeEnum(str, Enum):
    BUDGET = "BUDGET"
    FORECAST = "FORECAST"
    ACTUAL = "ACTUAL"
    SCENARIO = "SCENARIO"

# Custom types with validation
def validate_currency_code(v: str) -> str:
    """Validate currency code is 3 uppercase letters"""
    if v and not re.match(r'^[A-Z]{3}$', v.upper()):
        raise ValueError('Currency code must be 3 letters (e.g., USD, EUR)')
    return v.upper()

CurrencyCode = Annotated[str, BeforeValidator(validate_currency_code)]

# Base schemas
class CompanyBase(BaseModel):
    """Base schema for Company with common fields and validation"""
    code: str = Field(
        ..., 
        max_length=50,
        description="Unique company code",
        examples=["ACME", "CORP01"]
    )
    name: str = Field(
        ..., 
        max_length=255,
        description="Company full name",
        examples=["Acme Corporation", "Global Industries Inc."]
    )
    currency_code: CurrencyCode = Field(
        ...,
        max_length=3,
        description="ISO 4217 currency code",
        examples=["USD", "EUR", "GBP"]
    )
    fiscal_year_start_month: Optional[int] = Field(
        None, 
        ge=1, 
        le=12,
        description="Month when fiscal year starts (1-12)",
        examples=[1, 4, 7]
    )
    is_active: bool = Field(
        default=True,
        description="Whether the company is active"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Ensure code is uppercase and alphanumeric"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Code must be alphanumeric (can include _ or -)')
        return v.upper()

class CompanyCreate(CompanyBase):
    """Schema for creating a new company"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "ACME",
                "name": "Acme Corporation",
                "currency_code": "USD",
                "fiscal_year_start_month": 1,
                "is_active": True
            }
        }
    )

class CompanyUpdate(BaseModel):
    """Schema for updating company - all fields optional"""
    code: Optional[str] = Field(None, max_length=50, description="Company code")
    name: Optional[str] = Field(None, max_length=255, description="Company name")
    currency_code: Optional[CurrencyCode] = Field(None, max_length=3, description="Currency code")
    fiscal_year_start_month: Optional[int] = Field(None, ge=1, le=12, description="Fiscal year start")
    is_active: Optional[bool] = Field(None, description="Active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Corporation Updated",
                "is_active": True
            }
        }
    )

class CompanyResponse(CompanyBase):
    """Response schema for Company with all fields"""
    id: UUID = Field(description="Unique identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "code": "ACME",
                "name": "Acme Corporation",
                "currency_code": "USD",
                "fiscal_year_start_month": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

# Cost Center schemas
class CostCenterBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: bool = True

class CostCenterCreate(CostCenterBase):
    company_id: UUID

class CostCenterUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class CostCenterResponse(CostCenterBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# GL Account schemas
class GLAccountBase(BaseModel):
    """Base schema for General Ledger Account"""
    account_number: str = Field(
        ...,
        max_length=50,
        description="Account number/code",
        examples=["1000", "4000-01", "5100"]
    )
    name: str = Field(
        ...,
        max_length=255,
        description="Account name",
        examples=["Cash", "Sales Revenue", "Salaries Expense"]
    )
    account_type: AccountTypeEnum = Field(
        ...,
        description="Type of account (asset, liability, equity, revenue, expense)"
    )
    account_subtype: Optional[AccountSubtypeEnum] = Field(
        None,
        description="Subtype for more detailed classification"
    )
    parent_id: Optional[UUID] = Field(
        None,
        description="Parent account ID for hierarchical structure"
    )
    is_summary: bool = Field(
        default=False,
        description="Whether this is a summary/header account"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account is active"
    )
    
    @field_validator('account_number')
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Validate account number format"""
        if not v.replace('-', '').replace('.', '').isalnum():
            raise ValueError('Account number must be alphanumeric (can include - or .)')
        return v

class GLAccountCreate(GLAccountBase):
    company_id: UUID

class GLAccountUpdate(BaseModel):
    account_number: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    account_type: Optional[AccountTypeEnum] = None
    account_subtype: Optional[AccountSubtypeEnum] = None
    parent_id: Optional[UUID] = None
    is_summary: Optional[bool] = None
    is_active: Optional[bool] = None

class GLAccountResponse(GLAccountBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Fiscal Period schemas
class FiscalPeriodBase(BaseModel):
    fiscal_year: int
    period_number: int = Field(..., ge=1, le=12)
    period_name: str = Field(..., max_length=50)
    start_date: date
    end_date: date
    is_closed: bool = False

class FiscalPeriodCreate(FiscalPeriodBase):
    company_id: UUID

class FiscalPeriodUpdate(BaseModel):
    period_name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_closed: Optional[bool] = None

class FiscalPeriodResponse(FiscalPeriodBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Scenario schemas
class ScenarioBase(BaseModel):
    name: str = Field(..., max_length=255)
    scenario_type: ScenarioTypeEnum
    fiscal_year: int
    version: int = 1
    is_approved: bool = False
    is_locked: bool = False

class ScenarioCreate(ScenarioBase):
    company_id: UUID
    created_by: Optional[UUID] = None

class ScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    is_approved: Optional[bool] = None
    is_locked: Optional[bool] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

class ScenarioResponse(ScenarioBase):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Budget Line schemas
class BudgetLineBase(BaseModel):
    amount: Decimal = Field(...)
    quantity: Optional[Decimal] = Field(None)
    rate: Optional[Decimal] = Field(None)
    notes: Optional[str] = None

class BudgetLineCreate(BudgetLineBase):
    scenario_id: UUID
    gl_account_id: UUID
    cost_center_id: UUID
    fiscal_period_id: UUID
    created_by: Optional[UUID] = None

class BudgetLineUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None)
    quantity: Optional[Decimal] = Field(None)
    rate: Optional[Decimal] = Field(None)
    notes: Optional[str] = None

class BudgetLineResponse(BudgetLineBase):
    id: UUID
    scenario_id: UUID
    gl_account_id: UUID
    cost_center_id: UUID
    fiscal_period_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# GL Transaction schemas  
class GLTransactionBase(BaseModel):
    """Base schema for General Ledger Transaction"""
    transaction_date: date = Field(
        ...,
        description="Transaction date",
        examples=["2024-01-15"]
    )
    reference_number: Optional[str] = Field(
        None,
        max_length=100,
        description="Reference/document number",
        examples=["INV-2024-001", "JE-2024-0123"]
    )
    description: Optional[str] = Field(
        None,
        description="Transaction description",
        examples=["Monthly rent payment", "Sales invoice #1234"]
    )
    source_system: Optional[str] = Field(
        None,
        max_length=100,
        description="Source system identifier",
        examples=["SALES", "PAYROLL", "MANUAL"]
    )
    external_id: Optional[str] = Field(
        None,
        max_length=255,
        description="External system reference ID"
    )
    is_posted: bool = Field(
        default=False,
        description="Whether transaction is posted to GL"
    )

class GLTransactionLineCreate(BaseModel):
    """Schema for creating GL transaction lines"""
    gl_account_id: UUID = Field(
        ...,
        description="GL Account ID"
    )
    cost_center_id: UUID = Field(
        ...,
        description="Cost Center ID"
    )
    debit_amount: Decimal = Field(
        default=Decimal('0'),
        ge=0,
        description="Debit amount (must be >= 0)",
        examples=[Decimal('1000.00'), Decimal('0')]
    )
    credit_amount: Decimal = Field(
        default=Decimal('0'),
        ge=0,
        description="Credit amount (must be >= 0)",
        examples=[Decimal('1000.00'), Decimal('0')]
    )
    description: Optional[str] = Field(
        None,
        description="Line item description"
    )
    
    @model_validator(mode='after')
    def validate_amounts(self) -> 'GLTransactionLineCreate':
        """Ensure either debit or credit is non-zero, but not both"""
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValueError('Either debit_amount or credit_amount must be non-zero')
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError('Cannot have both debit and credit amounts on same line')
        return self

class GLTransactionCreate(GLTransactionBase):
    """Schema for creating GL transactions with validation"""
    company_id: UUID = Field(..., description="Company ID")
    fiscal_period_id: UUID = Field(..., description="Fiscal Period ID")
    created_by: Optional[UUID] = Field(None, description="User who created the transaction")
    lines: List[GLTransactionLineCreate] = Field(
        ...,
        min_length=2,
        description="Transaction lines (minimum 2 for double-entry)"
    )
    
    @model_validator(mode='after')
    def validate_balanced_transaction(self) -> 'GLTransactionCreate':
        """Ensure transaction is balanced (total debits = total credits)"""
        total_debits = sum(line.debit_amount for line in self.lines)
        total_credits = sum(line.credit_amount for line in self.lines)
        
        if total_debits != total_credits:
            raise ValueError(
                f'Transaction must be balanced. Debits: {total_debits}, Credits: {total_credits}'
            )
        
        if total_debits == 0:
            raise ValueError('Transaction must have at least one debit and one credit')
        
        return self

class GLTransactionUpdate(BaseModel):
    transaction_date: Optional[date] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_posted: Optional[bool] = None

class GLTransactionLineResponse(BaseModel):
    id: UUID
    gl_account_id: UUID
    cost_center_id: UUID
    debit_amount: Decimal
    credit_amount: Decimal
    description: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class GLTransactionResponse(GLTransactionBase):
    id: UUID
    company_id: UUID
    fiscal_period_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    transaction_lines: List[GLTransactionLineResponse]
    
    model_config = ConfigDict(from_attributes=True)

# KPI schemas
class KPIBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    formula: Optional[str] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = Field(None)
    is_higher_better: bool = True
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class KPICreate(KPIBase):
    company_id: UUID

class KPIUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    formula: Optional[str] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = Field(None)
    is_higher_better: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class KPIResponse(KPIBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# User schemas
class UserBase(BaseModel):
    email: str = Field(..., max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Pagination
class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class PaginatedResponse(BaseModel):
    items: List
    total: int
    skip: int
    limit: int