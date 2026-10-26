from pydantic import BaseModel


class ClaimCreate(BaseModel):
    claimant_name: str
    policy_number: str
    claim_type: str