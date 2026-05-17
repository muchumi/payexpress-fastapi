from pydantic import BaseModel, ConfigDict
from typing import List
from .transactionHistoryResponse import TransactionHistoryResponse

class PaginatedTransactionResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[TransactionHistoryResponse]
    
    model_config=ConfigDict(from_attributes = True) 
        
    