"""PostgreSQL optimizations and best practices

Revision ID: 002_postgresql_optimizations
Revises: 001_initial
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers
revision = '002_postgresql_optimizations'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Apply PostgreSQL best practices and optimizations"""
    
    # ============================================
    # PERFORMANCE INDEXES
    # ============================================
    
    # Companies table indexes
    op.create_index(
        'idx_companies_code', 
        'companies', 
        ['code'],
        unique=True,
        postgresql_using='btree'
    )
    op.create_index(
        'idx_companies_active', 
        'companies', 
        ['is_active'],
        postgresql_where=sa.text('is_active = true')  # Partial index for active companies
    )
    
    # Cost Centers indexes
    op.create_index(
        'idx_cost_centers_company_code', 
        'cost_centers', 
        ['company_id', 'code'],
        unique=True
    )
    op.create_index(
        'idx_cost_centers_parent', 
        'cost_centers', 
        ['parent_id'],
        postgresql_where=sa.text('parent_id IS NOT NULL')  # Partial index
    )
    op.create_index(
        'idx_cost_centers_active_company', 
        'cost_centers', 
        ['company_id', 'is_active'],
        postgresql_where=sa.text('is_active = true')
    )
    
    # GL Accounts indexes
    op.create_index(
        'idx_gl_accounts_company_number', 
        'gl_accounts', 
        ['company_id', 'account_number'],
        unique=True
    )
    op.create_index(
        'idx_gl_accounts_type', 
        'gl_accounts', 
        ['company_id', 'account_type']
    )
    op.create_index(
        'idx_gl_accounts_parent', 
        'gl_accounts', 
        ['parent_id'],
        postgresql_where=sa.text('parent_id IS NOT NULL')
    )
    op.create_index(
        'idx_gl_accounts_active', 
        'gl_accounts', 
        ['company_id', 'is_active', 'account_type'],
        postgresql_where=sa.text('is_active = true')
    )
    
    # Fiscal Periods indexes
    op.create_index(
        'idx_fiscal_periods_company_year', 
        'fiscal_periods', 
        ['company_id', 'fiscal_year']
    )
    op.create_index(
        'idx_fiscal_periods_dates', 
        'fiscal_periods', 
        ['company_id', 'start_date', 'end_date']
    )
    op.create_index(
        'idx_fiscal_periods_open', 
        'fiscal_periods', 
        ['company_id', 'is_closed'],
        postgresql_where=sa.text('is_closed = false')
    )
    
    # Scenarios indexes
    op.create_index(
        'idx_scenarios_company_type_year', 
        'scenarios', 
        ['company_id', 'scenario_type', 'fiscal_year']
    )
    op.create_index(
        'idx_scenarios_approved', 
        'scenarios', 
        ['company_id', 'is_approved'],
        postgresql_where=sa.text('is_approved = true')
    )
    
    # Budget Lines indexes (critical for performance)
    op.create_index(
        'idx_budget_lines_scenario_account', 
        'budget_lines', 
        ['scenario_id', 'gl_account_id']
    )
    op.create_index(
        'idx_budget_lines_scenario_period', 
        'budget_lines', 
        ['scenario_id', 'fiscal_period_id']
    )
    op.create_index(
        'idx_budget_lines_account_period', 
        'budget_lines', 
        ['gl_account_id', 'fiscal_period_id']
    )
    
    # GL Transactions indexes
    op.create_index(
        'idx_gl_transactions_date', 
        'gl_transactions', 
        ['company_id', 'transaction_date']
    )
    op.create_index(
        'idx_gl_transactions_period', 
        'gl_transactions', 
        ['company_id', 'fiscal_period_id']
    )
    op.create_index(
        'idx_gl_transactions_posted', 
        'gl_transactions', 
        ['company_id', 'is_posted'],
        postgresql_where=sa.text('is_posted = true')
    )
    op.create_index(
        'idx_gl_transactions_reference', 
        'gl_transactions', 
        ['company_id', 'reference_number'],
        postgresql_where=sa.text('reference_number IS NOT NULL')
    )
    
    # GL Transaction Lines indexes
    op.create_index(
        'idx_gl_transaction_lines_account', 
        'gl_transaction_lines', 
        ['gl_account_id', 'gl_transaction_id']
    )
    op.create_index(
        'idx_gl_transaction_lines_cost_center', 
        'gl_transaction_lines', 
        ['cost_center_id', 'gl_transaction_id']
    )
    
    # ============================================
    # CHECK CONSTRAINTS
    # ============================================
    
    # Add check constraints for data integrity
    op.create_check_constraint(
        'ck_companies_fiscal_year_month',
        'companies',
        'fiscal_year_start_month BETWEEN 1 AND 12'
    )
    
    op.create_check_constraint(
        'ck_fiscal_periods_dates',
        'fiscal_periods',
        'end_date > start_date'
    )
    
    op.create_check_constraint(
        'ck_fiscal_periods_number',
        'fiscal_periods',
        'period_number BETWEEN 1 AND 12'
    )
    
    op.create_check_constraint(
        'ck_budget_lines_amount',
        'budget_lines',
        'amount IS NOT NULL'
    )
    
    op.create_check_constraint(
        'ck_gl_transaction_lines_amounts',
        'gl_transaction_lines',
        '(debit_amount > 0 AND credit_amount = 0) OR (debit_amount = 0 AND credit_amount > 0) OR (debit_amount = 0 AND credit_amount = 0)'
    )
    
    # ============================================
    # AUDIT COLUMNS AND TRIGGERS
    # ============================================
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to all tables with updated_at
    tables_with_updated_at = [
        'companies', 'cost_centers', 'gl_accounts', 'fiscal_periods',
        'scenarios', 'budget_lines', 'gl_transactions', 'gl_transaction_lines'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table}
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # ============================================
    # VALIDATION TRIGGERS
    # ============================================
    
    # Create GL Transaction balance validation trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_gl_transaction_balance()
        RETURNS TRIGGER AS $$
        DECLARE
            total_debits NUMERIC;
            total_credits NUMERIC;
        BEGIN
            -- Only validate for posted transactions
            IF NEW.is_posted = true THEN
                SELECT 
                    COALESCE(SUM(debit_amount), 0),
                    COALESCE(SUM(credit_amount), 0)
                INTO total_debits, total_credits
                FROM gl_transaction_lines
                WHERE gl_transaction_id = NEW.id;
                
                IF total_debits != total_credits THEN
                    RAISE EXCEPTION 'Transaction is not balanced. Debits: %, Credits: %', 
                        total_debits, total_credits;
                END IF;
                
                IF total_debits = 0 THEN
                    RAISE EXCEPTION 'Transaction has no amounts';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER validate_gl_transaction_balance_trigger
        BEFORE UPDATE ON gl_transactions
        FOR EACH ROW
        WHEN (NEW.is_posted = true)
        EXECUTE FUNCTION validate_gl_transaction_balance();
    """)
    
    # ============================================
    # MATERIALIZED VIEWS FOR ANALYTICS
    # ============================================
    
    # Create materialized view for account balances
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_account_balances AS
        SELECT 
            a.company_id,
            a.id as gl_account_id,
            a.account_number,
            a.name as account_name,
            a.account_type,
            fp.id as fiscal_period_id,
            fp.fiscal_year,
            fp.period_number,
            COALESCE(SUM(
                CASE 
                    WHEN a.account_type IN ('asset', 'expense') THEN 
                        tl.debit_amount - tl.credit_amount
                    ELSE 
                        tl.credit_amount - tl.debit_amount
                END
            ), 0) as balance
        FROM gl_accounts a
        CROSS JOIN fiscal_periods fp
        LEFT JOIN gl_transactions t ON 
            t.company_id = a.company_id 
            AND t.fiscal_period_id = fp.id
            AND t.is_posted = true
        LEFT JOIN gl_transaction_lines tl ON 
            tl.gl_transaction_id = t.id 
            AND tl.gl_account_id = a.id
        WHERE fp.company_id = a.company_id
        GROUP BY 
            a.company_id, a.id, a.account_number, a.name, 
            a.account_type, fp.id, fp.fiscal_year, fp.period_number;
    """)
    
    # Create index on materialized view
    op.execute("""
        CREATE INDEX idx_mv_account_balances_lookup 
        ON mv_account_balances (company_id, fiscal_period_id, gl_account_id);
    """)
    
    # Create refresh function for materialized view
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_account_balances()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_account_balances;
        END;
        $$ language 'plpgsql';
    """)
    
    # ============================================
    # PARTITIONING FOR LARGE TABLES
    # ============================================
    
    # Create partitioned table for transaction history (for scalability)
    op.execute("""
        -- Create parent table for partitioning
        CREATE TABLE IF NOT EXISTS gl_transactions_partitioned (
            LIKE gl_transactions INCLUDING ALL
        ) PARTITION BY RANGE (transaction_date);
        
        -- Create partitions for current and past years
        CREATE TABLE IF NOT EXISTS gl_transactions_y2024 
        PARTITION OF gl_transactions_partitioned
        FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
        
        CREATE TABLE IF NOT EXISTS gl_transactions_y2025 
        PARTITION OF gl_transactions_partitioned
        FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
    """)
    
    # ============================================
    # PERFORMANCE SETTINGS
    # ============================================
    
    # Add table statistics for better query planning
    op.execute("ALTER TABLE gl_transaction_lines SET (fillfactor = 90);")
    op.execute("ALTER TABLE budget_lines SET (fillfactor = 85);")
    
    # ============================================
    # CUSTOM FUNCTIONS FOR BUSINESS LOGIC
    # ============================================
    
    # Function to calculate running balance
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_running_balance(
            p_account_id UUID,
            p_end_date DATE
        )
        RETURNS NUMERIC AS $$
        DECLARE
            v_balance NUMERIC;
            v_account_type TEXT;
        BEGIN
            SELECT account_type INTO v_account_type
            FROM gl_accounts WHERE id = p_account_id;
            
            SELECT COALESCE(SUM(
                CASE 
                    WHEN v_account_type IN ('asset', 'expense') THEN 
                        tl.debit_amount - tl.credit_amount
                    ELSE 
                        tl.credit_amount - tl.debit_amount
                END
            ), 0) INTO v_balance
            FROM gl_transaction_lines tl
            JOIN gl_transactions t ON t.id = tl.gl_transaction_id
            WHERE tl.gl_account_id = p_account_id
                AND t.transaction_date <= p_end_date
                AND t.is_posted = true;
            
            RETURN v_balance;
        END;
        $$ language 'plpgsql' STABLE;
    """)
    
    # Function to get budget vs actual variance
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_budget_variance(
            p_scenario_id UUID,
            p_period_id UUID
        )
        RETURNS TABLE (
            gl_account_id UUID,
            budget_amount NUMERIC,
            actual_amount NUMERIC,
            variance NUMERIC,
            variance_pct NUMERIC
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                b.gl_account_id,
                b.amount as budget_amount,
                COALESCE(SUM(
                    CASE 
                        WHEN a.account_type IN ('revenue', 'liability', 'equity') THEN 
                            tl.credit_amount - tl.debit_amount
                        ELSE 
                            tl.debit_amount - tl.credit_amount
                    END
                ), 0) as actual_amount,
                COALESCE(SUM(
                    CASE 
                        WHEN a.account_type IN ('revenue', 'liability', 'equity') THEN 
                            tl.credit_amount - tl.debit_amount
                        ELSE 
                            tl.debit_amount - tl.credit_amount
                    END
                ), 0) - b.amount as variance,
                CASE 
                    WHEN b.amount = 0 THEN 0
                    ELSE ((COALESCE(SUM(
                        CASE 
                            WHEN a.account_type IN ('revenue', 'liability', 'equity') THEN 
                                tl.credit_amount - tl.debit_amount
                            ELSE 
                                tl.debit_amount - tl.credit_amount
                        END
                    ), 0) - b.amount) / b.amount * 100)
                END as variance_pct
            FROM budget_lines b
            JOIN gl_accounts a ON a.id = b.gl_account_id
            LEFT JOIN gl_transactions t ON 
                t.fiscal_period_id = p_period_id 
                AND t.is_posted = true
            LEFT JOIN gl_transaction_lines tl ON 
                tl.gl_transaction_id = t.id 
                AND tl.gl_account_id = b.gl_account_id
            WHERE b.scenario_id = p_scenario_id 
                AND b.fiscal_period_id = p_period_id
            GROUP BY b.gl_account_id, b.amount, a.account_type;
        END;
        $$ language 'plpgsql' STABLE;
    """)
    
    # ============================================
    # ROW LEVEL SECURITY (RLS)
    # ============================================
    
    # Enable RLS on sensitive tables
    op.execute("ALTER TABLE companies ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE gl_transactions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE budget_lines ENABLE ROW LEVEL SECURITY;")
    
    # Create policies (example - adjust based on your auth system)
    op.execute("""
        CREATE POLICY company_isolation ON companies
        FOR ALL
        USING (
            -- Users can only see their assigned companies
            id IN (
                SELECT company_id 
                FROM user_companies 
                WHERE user_id = current_setting('app.current_user_id')::UUID
            )
        );
    """)


def downgrade():
    """Remove PostgreSQL optimizations"""
    
    # Drop policies
    op.execute("DROP POLICY IF EXISTS company_isolation ON companies;")
    
    # Disable RLS
    op.execute("ALTER TABLE companies DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE gl_transactions DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE budget_lines DISABLE ROW LEVEL SECURITY;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS calculate_budget_variance;")
    op.execute("DROP FUNCTION IF EXISTS calculate_running_balance;")
    op.execute("DROP FUNCTION IF EXISTS refresh_account_balances;")
    
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_account_balances;")
    
    # Drop partitioned tables
    op.execute("DROP TABLE IF EXISTS gl_transactions_partitioned CASCADE;")
    
    # Drop triggers
    tables_with_updated_at = [
        'companies', 'cost_centers', 'gl_accounts', 'fiscal_periods',
        'scenarios', 'budget_lines', 'gl_transactions', 'gl_transaction_lines'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    op.execute("DROP TRIGGER IF EXISTS validate_gl_transaction_balance_trigger ON gl_transactions;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS validate_gl_transaction_balance;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")
    
    # Drop check constraints
    op.drop_constraint('ck_gl_transaction_lines_amounts', 'gl_transaction_lines')
    op.drop_constraint('ck_budget_lines_amount', 'budget_lines')
    op.drop_constraint('ck_fiscal_periods_number', 'fiscal_periods')
    op.drop_constraint('ck_fiscal_periods_dates', 'fiscal_periods')
    op.drop_constraint('ck_companies_fiscal_year_month', 'companies')
    
    # Drop all indexes
    op.drop_index('idx_gl_transaction_lines_cost_center', 'gl_transaction_lines')
    op.drop_index('idx_gl_transaction_lines_account', 'gl_transaction_lines')
    op.drop_index('idx_gl_transactions_reference', 'gl_transactions')
    op.drop_index('idx_gl_transactions_posted', 'gl_transactions')
    op.drop_index('idx_gl_transactions_period', 'gl_transactions')
    op.drop_index('idx_gl_transactions_date', 'gl_transactions')
    op.drop_index('idx_budget_lines_account_period', 'budget_lines')
    op.drop_index('idx_budget_lines_scenario_period', 'budget_lines')
    op.drop_index('idx_budget_lines_scenario_account', 'budget_lines')
    op.drop_index('idx_scenarios_approved', 'scenarios')
    op.drop_index('idx_scenarios_company_type_year', 'scenarios')
    op.drop_index('idx_fiscal_periods_open', 'fiscal_periods')
    op.drop_index('idx_fiscal_periods_dates', 'fiscal_periods')
    op.drop_index('idx_fiscal_periods_company_year', 'fiscal_periods')
    op.drop_index('idx_gl_accounts_active', 'gl_accounts')
    op.drop_index('idx_gl_accounts_parent', 'gl_accounts')
    op.drop_index('idx_gl_accounts_type', 'gl_accounts')
    op.drop_index('idx_gl_accounts_company_number', 'gl_accounts')
    op.drop_index('idx_cost_centers_active_company', 'cost_centers')
    op.drop_index('idx_cost_centers_parent', 'cost_centers')
    op.drop_index('idx_cost_centers_company_code', 'cost_centers')
    op.drop_index('idx_companies_active', 'companies')
    op.drop_index('idx_companies_code', 'companies')