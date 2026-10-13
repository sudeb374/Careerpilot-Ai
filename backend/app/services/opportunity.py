from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity

async def expire_overdue_opportunities(db: AsyncSession):
    """
    Transition Published opportunities with past deadlines to Expired status.
    """
    stmt = (
        update(Opportunity)
        .where(
            Opportunity.status == "Published",
            Opportunity.deadline.isnot(None),
            Opportunity.deadline < func.now()
        )
        .values(status="Expired")
    )
    result = await db.execute(stmt)
    rowcount = getattr(result, "rowcount", 0)
    if isinstance(rowcount, int) and rowcount > 0:
        await db.commit()
