from typing import Protocol

from sqlalchemy.orm import Session

from .models import SubscriptionEntitlement


class EntitlementProvider(Protocol):
    def get(self, db: Session, user_id: str) -> SubscriptionEntitlement: ...


class MockEntitlementProvider:
    """Local entitlement source; it never accepts a payment or client claim."""

    def get(self, db: Session, user_id: str) -> SubscriptionEntitlement:
        item = db.get(SubscriptionEntitlement, user_id)
        if item is None:
            item = SubscriptionEntitlement(user_id=user_id, plan="free", active=True, source="demo")
            db.add(item)
            db.flush()
        return item
