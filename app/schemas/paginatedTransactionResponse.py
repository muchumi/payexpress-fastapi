from pydantic import BaseModel
from typing import List
from .transactionHistoryResponse import TransactionHistoryResponse

class PaginatedTransactionResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[TransactionHistoryResponse]
    