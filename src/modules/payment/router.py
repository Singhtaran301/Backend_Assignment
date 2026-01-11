from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.core.database import get_db
from src.modules.payment.service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

# Schemas
class PaymentInitiate(BaseModel):
    booking_id: str
    amount: float

class WebhookPayload(BaseModel):
    transaction_id: str
    status: str # "SUCCESS" or "FAILED"

@router.post("/initiate")
async def initiate_payment(data: PaymentInitiate, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    payment = await service.create_payment_intent(data.booking_id, data.amount)
    if not payment:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"payment_id": payment.id, "transaction_id": payment.transaction_id, "status": "PENDING"}

@router.post("/webhook")
async def payment_webhook(
    payload: WebhookPayload, 
    x_signature: str = Header(None), # The Bank sends this header
    db: AsyncSession = Depends(get_db)
):
    """
    Simulates Stripe/Razorpay Webhook.
    """
    service = PaymentService(db)
    try:
        result = await service.process_webhook(payload.transaction_id, payload.status, x_signature)
        return result
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid Signature")