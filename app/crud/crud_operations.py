from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, select, func
from fastapi import HTTPException
from decimal import Decimal

from app.models.models import (
    Company, CostCenter, GLAccount, FiscalPeriod, 
    Scenario, BudgetLine, GLTransaction, GLTransactionLine,
    KPI, User
)
from app.schemas.schemas import (
    CompanyCreate, CompanyUpdate,
    CostCenterCreate, CostCenterUpdate,
    GLAccountCreate, GLAccountUpdate,
    FiscalPeriodCreate, FiscalPeriodUpdate,
    ScenarioCreate, ScenarioUpdate,
    BudgetLineCreate, BudgetLineUpdate,
    GLTransactionCreate, GLTransactionUpdate,
    KPICreate, KPIUpdate,
    UserCreate, UserUpdate
)
from .crud_base import CRUDBase

class CRUDCompany(CRUDBase[Company, CompanyCreate, CompanyUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[Company]:
        stmt = select(Company).where(Company.code == code)
        return db.execute(stmt).scalar_one_or_none()
    
    def get_active_companies(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Company]:
        stmt = select(Company).where(Company.is_active == True).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

class CRUDCostCenter(CRUDBase[CostCenter, CostCenterCreate, CostCenterUpdate]):
    def get_by_company_and_code(
        self, db: Session, *, company_id: UUID, code: str
    ) -> Optional[CostCenter]:
        stmt = select(CostCenter).where(
            and_(CostCenter.company_id == company_id, CostCenter.code == code)
        )
        return db.execute(stmt).scalar_one_or_none()
    
    def get_by_company(
        self, db: Session, *, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[CostCenter]:
        stmt = select(CostCenter).where(
            CostCenter.company_id == company_id
        ).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()
    
    def get_hierarchy(self, db: Session, *, company_id: UUID) -> List[CostCenter]:
        stmt = select(CostCenter).where(
            CostCenter.company_id == company_id
        ).order_by(CostCenter.parent_id.nullsfirst(), CostCenter.code)
        return db.execute(stmt).scalars().all()

class CRUDGLAccount(CRUDBase[GLAccount, GLAccountCreate, GLAccountUpdate]):
    def get_by_company_and_number(
        self, db: Session, *, company_id: UUID, account_number: str
    ) -> Optional[GLAccount]:
        stmt = select(GLAccount).where(
            and_(GLAccount.company_id == company_id, GLAccount.account_number == account_number)
        )
        return db.execute(stmt).scalar_one_or_none()
    
    def get_by_company(
        self, db: Session, *, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[GLAccount]:
        stmt = select(GLAccount).where(
            GLAccount.company_id == company_id
        ).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()
    
    def get_by_type(
        self, db: Session, *, company_id: UUID, account_type: str
    ) -> List[GLAccount]:
        stmt = select(GLAccount).where(
            and_(GLAccount.company_id == company_id, GLAccount.account_type == account_type)
        )
        return db.execute(stmt).scalars().all()

class CRUDFiscalPeriod(CRUDBase[FiscalPeriod, FiscalPeriodCreate, FiscalPeriodUpdate]):
    def get_by_company_and_period(
        self, db: Session, *, company_id: UUID, fiscal_year: int, period_number: int
    ) -> Optional[FiscalPeriod]:
        stmt = select(FiscalPeriod).where(
            and_(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.fiscal_year == fiscal_year,
                FiscalPeriod.period_number == period_number
            )
        )
        return db.execute(stmt).scalar_one_or_none()
    
    def get_by_company_and_year(
        self, db: Session, *, company_id: UUID, fiscal_year: int
    ) -> List[FiscalPeriod]:
        stmt = select(FiscalPeriod).where(
            and_(FiscalPeriod.company_id == company_id, FiscalPeriod.fiscal_year == fiscal_year)
        ).order_by(FiscalPeriod.period_number)
        return db.execute(stmt).scalars().all()
    
    def close_period(self, db: Session, *, id: UUID) -> FiscalPeriod:
        period = self.get(db, id=id)
        if not period:
            raise HTTPException(status_code=404, detail="Fiscal period not found")
        period.is_closed = True
        db.commit()
        db.refresh(period)
        return period

class CRUDScenario(CRUDBase[Scenario, ScenarioCreate, ScenarioUpdate]):
    def get_by_company_and_name(
        self, db: Session, *, company_id: UUID, name: str, fiscal_year: int
    ) -> Optional[Scenario]:
        return db.query(Scenario).filter(
            and_(
                Scenario.company_id == company_id,
                Scenario.name == name,
                Scenario.fiscal_year == fiscal_year
            )
        ).first()
    
    def get_approved_budget(
        self, db: Session, *, company_id: UUID, fiscal_year: int
    ) -> Optional[Scenario]:
        return db.query(Scenario).filter(
            and_(
                Scenario.company_id == company_id,
                Scenario.fiscal_year == fiscal_year,
                Scenario.scenario_type == "budget",
                Scenario.is_approved == True
            )
        ).first()
    
    def approve_scenario(
        self, db: Session, *, id: UUID, approved_by: UUID
    ) -> Scenario:
        scenario = self.get(db, id=id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        scenario.is_approved = True
        scenario.approved_by = approved_by
        scenario.approved_at = func.now()
        db.commit()
        db.refresh(scenario)
        return scenario

class CRUDBudgetLine(CRUDBase[BudgetLine, BudgetLineCreate, BudgetLineUpdate]):
    def get_by_scenario(
        self, db: Session, *, scenario_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[BudgetLine]:
        return db.query(BudgetLine).filter(
            BudgetLine.scenario_id == scenario_id
        ).offset(skip).limit(limit).all()
    
    def get_by_period_and_account(
        self, db: Session, *, 
        scenario_id: UUID, 
        fiscal_period_id: UUID, 
        gl_account_id: UUID
    ) -> List[BudgetLine]:
        return db.query(BudgetLine).filter(
            and_(
                BudgetLine.scenario_id == scenario_id,
                BudgetLine.fiscal_period_id == fiscal_period_id,
                BudgetLine.gl_account_id == gl_account_id
            )
        ).all()
    
    def get_total_by_period(
        self, db: Session, *, scenario_id: UUID, fiscal_period_id: UUID
    ) -> Decimal:
        result = db.query(func.sum(BudgetLine.amount)).filter(
            and_(
                BudgetLine.scenario_id == scenario_id,
                BudgetLine.fiscal_period_id == fiscal_period_id
            )
        ).scalar()
        return result or Decimal('0')

class CRUDGLTransaction(CRUDBase[GLTransaction, GLTransactionCreate, GLTransactionUpdate]):
    def create_with_lines(
        self, db: Session, *, obj_in: GLTransactionCreate
    ) -> GLTransaction:
        lines_data = obj_in.lines
        transaction_data = obj_in.model_dump(exclude={'lines'})
        
        # Validate that debits equal credits
        total_debits = sum(line.debit_amount for line in lines_data)
        total_credits = sum(line.credit_amount for line in lines_data)
        
        if total_debits != total_credits:
            raise HTTPException(
                status_code=400, 
                detail=f"Debits ({total_debits}) must equal credits ({total_credits})"
            )
        
        # Create transaction
        db_transaction = GLTransaction(**transaction_data)
        db.add(db_transaction)
        db.flush()
        
        # Create transaction lines
        for line_data in lines_data:
            line_dict = line_data.model_dump()
            db_line = GLTransactionLine(
                gl_transaction_id=db_transaction.id,
                **line_dict
            )
            db.add(db_line)
        
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    
    def post_transaction(self, db: Session, *, id: UUID) -> GLTransaction:
        transaction = self.get(db, id=id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        transaction.is_posted = True
        db.commit()
        db.refresh(transaction)
        return transaction
    
    def get_by_period(
        self, db: Session, *, fiscal_period_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[GLTransaction]:
        return db.query(GLTransaction).filter(
            GLTransaction.fiscal_period_id == fiscal_period_id
        ).offset(skip).limit(limit).all()

class CRUDKPI(CRUDBase[KPI, KPICreate, KPIUpdate]):
    def get_by_company_and_code(
        self, db: Session, *, company_id: UUID, code: str
    ) -> Optional[KPI]:
        return db.query(KPI).filter(
            and_(KPI.company_id == company_id, KPI.code == code)
        ).first()
    
    def get_by_company(
        self, db: Session, *, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[KPI]:
        return db.query(KPI).filter(
            KPI.company_id == company_id
        ).offset(skip).limit(limit).all()
    
    def get_by_category(
        self, db: Session, *, company_id: UUID, category: str
    ) -> List[KPI]:
        return db.query(KPI).filter(
            and_(KPI.company_id == company_id, KPI.category == category)
        ).all()

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def authenticate(self, db: Session, *, email: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user or not user.is_active:
            return None
        return user
    
    def update_last_login(self, db: Session, *, id: UUID) -> User:
        user = self.get(db, id=id)
        if user:
            user.last_login_at = func.now()
            db.commit()
            db.refresh(user)
        return user

# Initialize CRUD instances
crud_company = CRUDCompany(Company)
crud_cost_center = CRUDCostCenter(CostCenter)
crud_gl_account = CRUDGLAccount(GLAccount)
crud_fiscal_period = CRUDFiscalPeriod(FiscalPeriod)
crud_scenario = CRUDScenario(Scenario)
crud_budget_line = CRUDBudgetLine(BudgetLine)
crud_gl_transaction = CRUDGLTransaction(GLTransaction)
crud_kpi = CRUDKPI(KPI)
crud_user = CRUDUser(User)