from datetime import datetime, timezone
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, utcnow


async def expire_overdue_opportunities(
    db: AsyncSession,
    now: datetime | None = None,
) -> int:
    """
    Transition Published opportunities with past deadlines to Expired status.
    
    Guarantees:
    - Only opportunities with status == 'Published' are eligible for expiration.
    - Opportunities with status 'Draft', 'Closed', or already 'Expired' are NEVER modified.
    - Opportunities with deadline is NULL are NEVER expired (deadlines are not inferred).
    - Consistent UTC timezone handling.
    - Idempotent: repeated calls produce zero additional transitions.
    - Returns the number of opportunities transitioned to Expired.
    """
    if now is not None:
        if now.tzinfo is None:
            comparison_time = now.replace(tzinfo=timezone.utc)
        else:
            comparison_time = now
    else:
        comparison_time = func.now()

    stmt = (
        update(Opportunity)
        .where(
            Opportunity.status == "Published",
            Opportunity.deadline.isnot(None),
            Opportunity.deadline < comparison_time,
        )
        .values(
            status="Expired",
            updated_at=utcnow(),
        )
    )
    result = await db.execute(stmt)
    rowcount = getattr(result, "rowcount", 0)
    if isinstance(rowcount, int) and rowcount > 0:
        await db.commit()
        return rowcount
    return 0
