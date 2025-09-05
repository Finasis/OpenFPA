from fastapi import HTTPException, status

class CompanyNotFoundError(HTTPException):
    def __init__(self, company_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found"
        )

class DuplicateCompanyCodeError(HTTPException):
    def __init__(self, code: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with code {code} already exists"
        )

class UnbalancedTransactionError(HTTPException):
    def __init__(self, debits: float, credits: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is not balanced. Debits ({debits}) must equal credits ({credits})"
        )

class PeriodClosedError(HTTPException):
    def __init__(self, period_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot post to closed period {period_name}"
        )

class InsufficientPermissionsError(HTTPException):
    def __init__(self, action: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to {action}"
        )