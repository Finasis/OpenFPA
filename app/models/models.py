from sqlalchemy import (
    String, Integer, Boolean, DateTime, Date, 
    ForeignKey, Numeric, Text, Enum as SQLEnum, 
    CheckConstraint, UniqueConstraint, Index, func, select, Column
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, List
from datetime import datetime
import enum
import uuid
from .base import Base

class AccountType(enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class AccountSubtype(enum.Enum):
    OPERATING = "operating"
    NON_OPERATING = "non_operating"
    CAPITAL = "capital"
    OTHER = "other"

class ScenarioType(enum.Enum):
    BUDGET = "BUDGET"
    FORECAST = "FORECAST"
    ACTUAL = "ACTUAL"
    SCENARIO = "SCENARIO"

class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Company(Base):
    __tablename__ = "companies"
    
    # SQLAlchemy 2.0 style with mapped_column and type annotations
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, CheckConstraint('fiscal_year_start_month BETWEEN 1 AND 12'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with type hints
    cost_centers: Mapped[List["CostCenter"]] = relationship("CostCenter", back_populates="company", cascade="all, delete-orphan")
    gl_accounts: Mapped[List["GLAccount"]] = relationship("GLAccount", back_populates="company", cascade="all, delete-orphan")
    fiscal_periods: Mapped[List["FiscalPeriod"]] = relationship("FiscalPeriod", back_populates="company", cascade="all, delete-orphan")
    scenarios: Mapped[List["Scenario"]] = relationship("Scenario", back_populates="company", cascade="all, delete-orphan")

class CostCenter(Base):
    __tablename__ = "cost_centers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code'),
    )
    
    company: Mapped["Company"] = relationship("Company", back_populates="cost_centers")
    parent: Mapped[Optional["CostCenter"]] = relationship("CostCenter", remote_side=[id], backref="children")

class GLAccount(Base):
    __tablename__ = "gl_accounts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(SQLEnum(AccountType), nullable=False)
    account_subtype: Mapped[Optional[AccountSubtype]] = mapped_column(SQLEnum(AccountSubtype), nullable=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=True)
    is_summary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'account_number'),
    )
    
    company: Mapped["Company"] = relationship("Company", back_populates="gl_accounts")
    parent: Mapped[Optional["GLAccount"]] = relationship("GLAccount", remote_side=[id], backref="children")

class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False, info={'check_constraint': 'period_number BETWEEN 1 AND 12'})
    period_name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'fiscal_year', 'period_number'),
        CheckConstraint('period_number BETWEEN 1 AND 12'),
    )
    
    company: Mapped["Company"] = relationship("Company", back_populates="fiscal_periods")

class Scenario(Base):
    __tablename__ = "scenarios"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[ScenarioType] = mapped_column(SQLEnum(ScenarioType), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'name', 'fiscal_year', 'version'),
    )
    
    company: Mapped["Company"] = relationship("Company", back_populates="scenarios")
    budget_lines: Mapped[List["BudgetLine"]] = relationship("BudgetLine", back_populates="scenario", cascade="all, delete-orphan")

class BudgetLine(Base):
    __tablename__ = "budget_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"))
    gl_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"))
    cost_center_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    fiscal_period_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    rate: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('scenario_id', 'gl_account_id', 'cost_center_id', 'fiscal_period_id'),
    )
    
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="budget_lines")
    gl_account: Mapped["GLAccount"] = relationship("GLAccount")
    cost_center: Mapped["CostCenter"] = relationship("CostCenter")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod")

class GLTransaction(Base):
    __tablename__ = "gl_transactions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    transaction_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company")
    fiscal_period: Mapped[Optional["FiscalPeriod"]] = relationship("FiscalPeriod")
    transaction_lines: Mapped[List["GLTransactionLine"]] = relationship("GLTransactionLine", back_populates="transaction", cascade="all, delete-orphan")

class GLTransactionLine(Base):
    __tablename__ = "gl_transaction_lines"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gl_transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_transactions.id", ondelete="CASCADE"))
    gl_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"))
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    debit_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    credit_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('debit_amount >= 0 AND credit_amount >= 0'),
        CheckConstraint('debit_amount = 0 OR credit_amount = 0'),
    )
    
    transaction: Mapped["GLTransaction"] = relationship("GLTransaction", back_populates="transaction_lines")
    gl_account: Mapped["GLAccount"] = relationship("GLAccount")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

class KPI(Base):
    __tablename__ = "kpis"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    is_higher_better: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code'),
    )
    
    company: Mapped["Company"] = relationship("Company")
    kpi_actuals: Mapped[List["KPIActual"]] = relationship("KPIActual", back_populates="kpi", cascade="all, delete-orphan")

class KPIActual(Base):
    __tablename__ = "kpi_actuals"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("kpis.id", ondelete="CASCADE"))
    fiscal_period_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))
    actual_value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('kpi_id', 'fiscal_period_id'),
    )
    
    kpi: Mapped["KPI"] = relationship("KPI", back_populates="kpi_actuals")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod")

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company_access: Mapped[List["UserCompanyAccess"]] = relationship("UserCompanyAccess", back_populates="user", cascade="all, delete-orphan")

class UserCompanyAccess(Base):
    __tablename__ = "user_company_access"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id'),
    )
    
    user: Mapped["User"] = relationship("User", back_populates="company_access")
    company: Mapped["Company"] = relationship("Company")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company")

# ============================================
# ANALYTICS & FORECASTING MODELS
# ============================================

class ForecastModel(Base):
    __tablename__ = "forecast_models"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'linear_regression', 'moving_average', 'seasonal', 'driver_based'
    gl_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    configuration: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Model-specific parameters
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    accuracy_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)  # R-squared or similar metric
    last_trained_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'name'),
    )
    
    company: Mapped["Company"] = relationship("Company")
    gl_account: Mapped[Optional["GLAccount"]] = relationship("GLAccount")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")
    forecast_results: Mapped[List["ForecastResult"]] = relationship("ForecastResult", back_populates="forecast_model", cascade="all, delete-orphan")

class ForecastResult(Base):
    __tablename__ = "forecast_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forecast_models.id", ondelete="CASCADE"))
    fiscal_period_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))
    forecasted_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    confidence_interval_low: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    confidence_interval_high: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('forecast_model_id', 'fiscal_period_id'),
    )
    
    forecast_model: Mapped["ForecastModel"] = relationship("ForecastModel", back_populates="forecast_results")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod")

class BusinessDriver(Base):
    __tablename__ = "business_drivers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 'volume', 'price', 'efficiency', 'external'
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)  # External factors like inflation, currency rates
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code'),
    )
    
    company: Mapped["Company"] = relationship("Company")
    driver_values: Mapped[List["DriverValue"]] = relationship("DriverValue", back_populates="business_driver", cascade="all, delete-orphan")
    relationships: Mapped[List["DriverRelationship"]] = relationship("DriverRelationship", back_populates="business_driver", cascade="all, delete-orphan")

class DriverValue(Base):
    __tablename__ = "driver_values"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_drivers.id", ondelete="CASCADE"))
    fiscal_period_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))
    scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=True)  # NULL for actuals
    actual_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    planned_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('business_driver_id', 'fiscal_period_id', 'scenario_id'),
    )
    
    business_driver: Mapped["BusinessDriver"] = relationship("BusinessDriver", back_populates="driver_values")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod")
    scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")

class DriverRelationship(Base):
    __tablename__ = "driver_relationships"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("business_drivers.id", ondelete="CASCADE"))
    gl_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id", ondelete="CASCADE"))
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'linear', 'percentage', 'step_function', 'custom_formula'
    coefficient: Mapped[Optional[float]] = mapped_column(Numeric(15, 6), nullable=True)  # Multiplier for linear relationships
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Custom formula for complex relationships
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    business_driver: Mapped["BusinessDriver"] = relationship("BusinessDriver", back_populates="relationships")
    gl_account: Mapped["GLAccount"] = relationship("GLAccount")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dashboard_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'executive', 'operational', 'variance', 'kpi'
    layout_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Widget positions, sizes, etc.
    filters_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Default filters
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company")
    widgets: Mapped[List["DashboardWidget"]] = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"))
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'kpi_card', 'chart', 'table', 'variance_analysis'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Widget-specific config (chart type, data source, etc.)
    position_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    refresh_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
    data_sources: Mapped[List["WidgetDataSource"]] = relationship("WidgetDataSource", back_populates="dashboard_widget", cascade="all, delete-orphan")

class WidgetDataSource(Base):
    __tablename__ = "widget_data_sources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_widget_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dashboard_widgets.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'kpi', 'gl_account', 'variance', 'forecast', 'custom_query'
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # ID of the source object
    configuration: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Source-specific config
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    dashboard_widget: Mapped["DashboardWidget"] = relationship("DashboardWidget", back_populates="data_sources")

# class VarianceExplanation(Base):
#     __tablename__ = "variance_explanations"
#     
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     variance_analysis_id = Column(UUID(as_uuid=True), ForeignKey("variance_analysis.id", ondelete="CASCADE"))
#     explanation_text = Column(Text, nullable=False)
#     impact_category = Column(String(50))  # 'volume', 'price', 'efficiency', 'timing', 'one_time'
#     corrective_action = Column(Text)
#     responsible_person = Column(UUID(as_uuid=True))
#     due_date = Column(Date)
#     status = Column(String(50), default='open')  # 'open', 'in_progress', 'resolved'
#     created_by = Column(UUID(as_uuid=True))
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     
#     variance_analysis = relationship("VarianceAnalysis")

class VarianceThreshold(Base):
    __tablename__ = "variance_thresholds"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    gl_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=True)
    threshold_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'percentage', 'absolute'
    warning_threshold: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    critical_threshold: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company")
    gl_account: Mapped[Optional["GLAccount"]] = relationship("GLAccount")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

class ScenarioAssumption(Base):
    __tablename__ = "scenario_assumptions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"))
    assumption_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'growth_rate', 'inflation', 'headcount', 'custom'
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    adjusted_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scenario: Mapped["Scenario"] = relationship("Scenario")

class ScenarioComparison(Base):
    __tablename__ = "scenario_comparisons"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=True)
    comparison_scenarios: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Array of scenario IDs
    comparison_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company")
    base_scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")