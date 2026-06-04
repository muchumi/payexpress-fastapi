from enum import Enum

class TransactionType(str, Enum):
    deposit="deposit"
    withdrawal="withdrawal"