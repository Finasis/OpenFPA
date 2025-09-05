#!/usr/bin/env python3
"""
Script to convert remaining Column() declarations to mapped_column() in models.py
This completes the SQLAlchemy 2.0 migration for all remaining models.
"""

import re
from pathlib import Path

def convert_models():
    """Convert remaining models to SQLAlchemy 2.0 style."""
    models_file = Path("/home/marioled/dev/claude/app/models/models.py")
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Define the remaining model conversions
    conversions = [
        # DashboardWidget
        {
            'old': '''class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"))
    widget_type = Column(String(50), nullable=False)  # 'kpi_card', 'chart', 'table', 'variance_analysis'
    title = Column(String(255), nullable=False)
    configuration = Column(JSONB)  # Widget-specific config (chart type, data source, etc.)
    position_x = Column(Integer)
    position_y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    refresh_interval = Column(Integer)  # Minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    dashboard = relationship("Dashboard", back_populates="widgets")
    data_sources = relationship("WidgetDataSource", back_populates="dashboard_widget", cascade="all, delete-orphan")''',
            'new': '''class DashboardWidget(Base):
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
    data_sources: Mapped[List["WidgetDataSource"]] = relationship("WidgetDataSource", back_populates="dashboard_widget", cascade="all, delete-orphan")'''
        },
        # WidgetDataSource
        {
            'old': '''class WidgetDataSource(Base):
    __tablename__ = "widget_data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_widget_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_widgets.id", ondelete="CASCADE"))
    source_type = Column(String(50), nullable=False)  # 'kpi', 'gl_account', 'variance', 'forecast', 'custom_query'
    source_id = Column(UUID(as_uuid=True))  # ID of the source object
    configuration = Column(JSONB)  # Source-specific config
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dashboard_widget = relationship("DashboardWidget", back_populates="data_sources")''',
            'new': '''class WidgetDataSource(Base):
    __tablename__ = "widget_data_sources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_widget_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dashboard_widgets.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'kpi', 'gl_account', 'variance', 'forecast', 'custom_query'
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # ID of the source object
    configuration: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Source-specific config
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    dashboard_widget: Mapped["DashboardWidget"] = relationship("DashboardWidget", back_populates="data_sources")'''
        },
        # VarianceThreshold
        {
            'old': '''class VarianceThreshold(Base):
    __tablename__ = "variance_thresholds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"))
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    threshold_type = Column(String(50), nullable=False)  # 'percentage', 'absolute'
    warning_threshold = Column(Numeric(15, 2), nullable=False)
    critical_threshold = Column(Numeric(15, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company")
    gl_account = relationship("GLAccount")
    cost_center = relationship("CostCenter")''',
            'new': '''class VarianceThreshold(Base):
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
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")'''
        },
        # ScenarioAssumption
        {
            'old': '''class ScenarioAssumption(Base):
    __tablename__ = "scenario_assumptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"))
    assumption_type = Column(String(50), nullable=False)  # 'growth_rate', 'inflation', 'headcount', 'custom'
    name = Column(String(255), nullable=False)
    base_value = Column(Numeric(15, 4))
    adjusted_value = Column(Numeric(15, 4))
    unit_of_measure = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scenario = relationship("Scenario")''',
            'new': '''class ScenarioAssumption(Base):
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
    
    scenario: Mapped["Scenario"] = relationship("Scenario")'''
        },
        # ScenarioComparison
        {
            'old': '''class ScenarioComparison(Base):
    __tablename__ = "scenario_comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    base_scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"))
    comparison_scenarios = Column(JSONB)  # Array of scenario IDs
    comparison_config = Column(JSONB)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company")
    base_scenario = relationship("Scenario")''',
            'new': '''class ScenarioComparison(Base):
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
    base_scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")'''
        }
    ]
    
    # Apply conversions
    for conversion in conversions:
        if conversion['old'] in content:
            content = content.replace(conversion['old'], conversion['new'])
            print(f"✓ Converted {conversion['old'].split('(')[0].split()[-1]} model")
        else:
            print(f"✗ Could not find {conversion['old'].split('(')[0].split()[-1]} model")
    
    # Write back the updated content
    with open(models_file, 'w') as f:
        f.write(content)
    
    print("✓ Completed SQLAlchemy 2.0 model conversions")

if __name__ == "__main__":
    convert_models()