from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.config.settings import get_settings
from src.api.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from sqlalchemy import select, update
from src.models.user import User
import stripe

settings = get_settings()
router = APIRouter()

stripe.api_key = settings.stripe_secret_key if hasattr(settings, 'stripe_secret_key') else ''

class CheckoutRequest(BaseModel):
    plan: str
    billing_cycle: str = 'monthly'

@router.post('/create-checkout-session')
async def create_checkout(req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    # Map plan to Stripe price IDs from settings
    price_map = {
        'professional_monthly': getattr(settings, 'stripe_price_professional_monthly', None),
        'professional_yearly': getattr(settings, 'stripe_price_professional_yearly', None),
    }

    key = None
    if req.plan == 'professional':
        key = f'professional_{req.billing_cycle}'
    else:
        raise HTTPException(status_code=400, detail='Unsupported plan')

    price_id = price_map.get(key)
    if not price_id:
        raise HTTPException(status_code=500, detail='Payment configuration missing')

    try:
        session = stripe.checkout.Session.create(
            success_url=f"{settings.app_host}:{settings.app_port}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_host}:{settings.app_port}/payment",
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            client_reference_id=str(current_user['id']),
            customer_email=current_user['email'],
        )
        return {'url': session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/webhook')
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = getattr(settings, 'stripe_webhook_secret', None)

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Webhook error: {e}')

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        email = session.get('customer_email')
        # Update user plan in DB
        async with get_db().__anext__() as db:  # get a db session
            q = select(User).where(User.id == int(client_reference_id))
            result = await db.execute(q)
            user = result.scalar_one_or_none()
            if user:
                # set plan to Professional
                user.plan = 'Professional'
                db.add(user)
                await db.commit()
    return {'status': 'ok'}
