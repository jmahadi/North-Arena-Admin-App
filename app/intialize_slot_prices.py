import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import SlotPrice, DayOfWeek
from app.config import settings

# Use the database URL from settings
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

time_slots = [
    "9:30 AM - 11:00 AM",
    "11:00 AM - 12:30 PM",
    "12:30 PM - 2:00 PM",
    "3:00 PM - 4:30 PM",
    "4:30 PM - 6:00 PM",
    "6:00 PM - 7:30 PM",
    "7:30 PM - 9:00 PM",
    "9:00 PM - 10:30 PM"
]

weekdays = [DayOfWeek.SUNDAY, DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY]
weekends = [DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY]

def get_price(day, slot):
    if day in weekdays:
        if slot == "9:30 AM - 11:00 AM":
            return 2500
        elif slot < "6:00 PM - 7:30 PM":
            return 2500
        else:
            return 3000
    else:  # weekends
        if slot < "6:00 PM - 7:30 PM":
            return 3000
        else:
            return 3500

async def add_slot_prices():
    async with AsyncSessionLocal() as session:
        # Clear existing slot prices
        await session.execute(SlotPrice.__table__.delete())

        # Add prices for all days
        for day in weekdays + weekends:
            for slot in time_slots:
                price = get_price(day, slot)
                new_price = SlotPrice(time_slot=slot, day_of_week=day, price=price, is_default=True)
                session.add(new_price)

        await session.commit()

    print("Slot prices have been initialized.")

if __name__ == "__main__":
    asyncio.run(add_slot_prices())