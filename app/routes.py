from fastapi import APIRouter, Depends, Request, Form, HTTPException , Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text , func
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime , timedelta  ,timezone , date
from dateutil.relativedelta import relativedelta
from .database import get_db
from .models import User , Booking , Transaction, SlotPrice, PaymentMethod , TransactionStatus , TransactionType , TransactionSummary, DayOfWeek
from .auth import create_access_token, get_current_user
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


'''
--------------------
INDEX ROUTE
--------------------
'''

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/login", status_code=303)

@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    user = User(username=username, email=email)
    user.set_password(password)
    db.add(user)
    await db.commit()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request,
                email: str = Form(...),
                password: str = Form(...),
                db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).filter(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

'''
--------------------
BOOKING ROUTE
--------------------
'''



@router.post("/book", response_class=JSONResponse)
async def book(
    request: Request, 
    name: str = Form(...), 
    phone: str = Form(...), 
    booking_date: str = Form(...), 
    time_slot: str = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    booking_date_parsed = datetime.strptime(booking_date, "%Y-%m-%d").date()
    existing_booking_result = await db.execute(select(Booking).filter(Booking.booking_date == booking_date_parsed, Booking.time_slot == time_slot))
    existing_booking = existing_booking_result.scalar_one_or_none()
    
    if existing_booking:
        return JSONResponse(content={
            "success": False,
            "message": "This slot is already booked"
        })
    else:
        booking = Booking(
            booked_by=current_user.id,
            name=name,
            phone=phone,
            booking_date=booking_date_parsed,
            time_slot=time_slot,
            last_modified_by=current_user.id
        )
        db.add(booking)
        await db.commit()
        message = "Slot has been successfully booked"

    # Handle date range
    today = datetime.now().date()
    
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = today
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = start_date + timedelta(days=6)
    
    # Ensure the range doesn't exceed 3 months
    max_end_date = start_date + relativedelta(months=3)
    end_date = min(end_date, max_end_date)

    # Fetch bookings for the selected date range
    bookings_result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.user))
        .filter(Booking.booking_date.between(start_date, end_date))
        .order_by(Booking.booking_date, Booking.time_slot)
    )
    bookings = bookings_result.scalars().all()

    # Create bookingsData dictionary
    bookings_data = {
        f"{booking.booking_date.isoformat()}_{booking.time_slot}": {
            "id": booking.id,
            "name": booking.name,
            "phone": booking.phone,
            "booking_date": booking.booking_date.isoformat(),
            "time_slot": booking.time_slot,
            "booked_by": booking.user.username
        }
        for booking in bookings
    }

    return JSONResponse(content={
        "success": True,
        "message": message,
        "bookingsData": bookings_data
    })



'''
--------------------
UPDATE BOOKING ROUTE
--------------------
'''

@router.post("/update_booking", response_class=JSONResponse)
async def update_booking(
    request: Request, 
    booking_id: int = Form(...), 
    name: str = Form(...), 
    phone: str = Form(...), 
    booking_date: str = Form(...), 
    time_slot: str = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    booking_result = await db.execute(select(Booking).filter(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        return JSONResponse(content={
            "success": False,
            "message": "Booking not found"
        })
    else:
        # Check if the new slot is already booked
        new_booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        existing_booking_result = await db.execute(
            select(Booking).filter(
                Booking.booking_date == new_booking_date,
                Booking.time_slot == time_slot,
                Booking.id != booking_id  # Exclude the current booking
            )
        )
        existing_booking = existing_booking_result.scalar_one_or_none()
        
        if existing_booking:
            return JSONResponse(content={
                "success": False,
                "message": "This slot is already booked. Please choose another."
            })
        else:
            booking.name = name
            booking.phone = phone
            booking.booking_date = new_booking_date
            booking.time_slot = time_slot
            booking.last_modified_by = current_user.id
            booking.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            message = "Booking updated successfully"

    # Handle date range
    today = datetime.now().date()
    
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = today
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = start_date + timedelta(days=6)
    
    # Ensure the range doesn't exceed 3 months
    max_end_date = start_date + relativedelta(months=3)
    end_date = min(end_date, max_end_date)

    # Fetch bookings for the selected date range
    bookings_result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.user))
        .filter(Booking.booking_date.between(start_date, end_date))
        .order_by(Booking.booking_date, Booking.time_slot)
    )
    bookings = bookings_result.scalars().all()

    # Create bookingsData dictionary
    bookings_data = {
        f"{booking.booking_date.isoformat()}_{booking.time_slot}": {
            "id": booking.id,
            "name": booking.name,
            "phone": booking.phone,
            "booking_date": booking.booking_date.isoformat(),
            "time_slot": booking.time_slot,
            "booked_by": booking.user.username
        }
        for booking in bookings
    }

    return JSONResponse(content={
        "success": True,
        "message": message,
        "bookingsData": bookings_data
    })



'''
--------------------
CLEAR BOOKING ROUTE
--------------------
'''

@router.delete("/delete_booking/{booking_id}", response_class=JSONResponse)
async def delete_booking(
    booking_id: int,
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    booking_result = await db.execute(select(Booking).filter(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        return JSONResponse(content={
            "success": False,
            "message": "Booking not found"
        }, status_code=404)
    
    await db.delete(booking)
    await db.commit()

    # Handle date range
    today = datetime.now().date()
    
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = today
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = start_date + timedelta(days=6)
    
    # Ensure the range doesn't exceed 3 months
    max_end_date = start_date + relativedelta(months=3)
    end_date = min(end_date, max_end_date)

    # Fetch bookings for the selected date range
    bookings_result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.user))
        .filter(Booking.booking_date.between(start_date, end_date))
        .order_by(Booking.booking_date, Booking.time_slot)
    )
    bookings = bookings_result.scalars().all()

    # Create updated bookingsData dictionary
    bookings_data = {
        f"{booking.booking_date.isoformat()}_{booking.time_slot}": {
            "id": booking.id,
            "name": booking.name,
            "phone": booking.phone,
            "booking_date": booking.booking_date.isoformat(),
            "time_slot": booking.time_slot,
            "booked_by": booking.user.username
        }
        for booking in bookings
    }

    return JSONResponse(content={
        "success": True,
        "message": "Booking deleted successfully",
        "bookingsData": bookings_data
    })


'''
--------------------
BOOKINGS PAGE ROUTE
--------------------
'''


@router.get("/bookings", response_class=HTMLResponse)
async def bookings(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    today = datetime.now().date()
    
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = today
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = start_date + timedelta(days=6)
    
    # Ensure the range doesn't exceed 3 months
    max_end_date = start_date + relativedelta(months=3)
    end_date = min(end_date, max_end_date)
    
    bookings_result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.user))
        .filter(Booking.booking_date.between(start_date, end_date))
        .order_by(Booking.booking_date, Booking.time_slot)
    )
    bookings = bookings_result.scalars().all()

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

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "current_user": current_user,
        "bookings": bookings,
        "date_range": date_range,
        "time_slots": time_slots,
        "start_date": start_date,
        "end_date": end_date,
        "today": today,
        "messages": []
    })



'''
--------------------
DASHBOARD ROUTE
--------------------
'''


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user
    })



'''
--------------------
SLOT PRICE ROUTE
--------------------
'''

@router.get("/slot_prices", response_class=HTMLResponse)
async def slot_prices_page(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("slot_prices.html", {"request": request, "current_user": current_user})

@router.get("/list_slot_prices", response_class=JSONResponse)
async def list_slot_prices(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(SlotPrice))
        slot_prices = result.scalars().all()
        return JSONResponse(content={
            "success": True,
            "slot_prices": [{
                "id": sp.id,
                "time_slot": sp.time_slot,
                "day_of_week": sp.day_of_week.value,
                "price": sp.price,
                "start_date": sp.start_date.isoformat() if sp.start_date else None,
                "end_date": sp.end_date.isoformat() if sp.end_date else None,
                "is_default": sp.is_default
            } for sp in slot_prices]
        })
    except Exception as exc:
        logging.error(f"Error fetching slot prices: {str(exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Error fetching slot prices: {str(exc)}"})

@router.post("/add_update_slot_price", response_class=JSONResponse)
async def add_update_slot_price(
    time_slot: str = Form(...),
    day_of_week: str = Form(...),
    price: float = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    is_default: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check if a slot price already exists for this time slot and day of week
        existing_slot_price = await db.execute(
            select(SlotPrice).filter(
                SlotPrice.time_slot == time_slot,
                SlotPrice.day_of_week == DayOfWeek[day_of_week]
            )
        )
        existing_slot_price = existing_slot_price.scalar_one_or_none()

        if existing_slot_price:
            # Update existing slot price
            existing_slot_price.price = price
            existing_slot_price.start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            existing_slot_price.end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            existing_slot_price.is_default = is_default
        else:
            # Create new slot price
            new_slot_price = SlotPrice(
                time_slot=time_slot,
                day_of_week=DayOfWeek[day_of_week],
                price=price,
                start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
                is_default=is_default
            )
            db.add(new_slot_price)

        await db.commit()
        return JSONResponse(content={"success": True, "message": "Slot price added/updated successfully"})
    except Exception as exc:
        await db.rollback()
        logging.error(f"Error adding/updating slot price: {str(exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Error adding/updating slot price: {str(exc)}"})




'''
--------------------
TRANSACTION ROUTE
--------------------
'''




@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("transactions.html", {"request": request, "current_user": current_user})

@router.get("/update_transactions", response_class=HTMLResponse)
async def update_transactions_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("update_transactions.html", {"request": request, "current_user": current_user})


@router.get("/bookings_for_date")
async def get_bookings_for_date(date: str, db: AsyncSession = Depends(get_db)):
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        bookings = await db.execute(
            select(Booking)
            .filter(Booking.booking_date == booking_date)
            .order_by(Booking.time_slot)
        )
        return [
            {
                "id": b.id,
                "name": b.name,
                "time_slot": b.time_slot,
            } for b in bookings.scalars()
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/transactions_list")
async def get_transactions(
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Transaction).options(joinedload(Transaction.booking), joinedload(Transaction.creator))
        
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Transaction.created_at >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Transaction.created_at <= end_date)
        
        query = query.order_by(Transaction.created_at.desc())
        
        transactions = await db.execute(query)
        
        result = [
            {
                "id": t.id,
                "booking_date": t.booking.booking_date.isoformat(),
                "time_slot": t.booking.time_slot,
                "transaction_type": t.transaction_type.value,
                "payment_method": t.payment_method.value,
                "amount": t.amount,
                "creator": t.creator.username,
                "created_at": t.created_at.isoformat()
            } for t in transactions.scalars()
        ]
        return JSONResponse(content={"success": True, "transactions": result})
    except SQLAlchemyError as e:
        logging.error(f"Database error in get_transactions: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Database error: {str(e)}"})
    except Exception as e:
        logging.error(f"Unexpected error in get_transactions: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Unexpected error: {str(e)}"})



@router.get("/transaction_details")
async def get_transaction_details(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        transaction = await db.execute(
            select(Transaction)
            .options(joinedload(Transaction.booking), joinedload(Transaction.creator))
            .filter(Transaction.id == transaction_id)
        )
        transaction = transaction.scalar_one_or_none()

        if not transaction:
            return JSONResponse(status_code=404, content={"success": False, "message": "Transaction not found"})

        return JSONResponse(content={
            "success": True,
            "transaction": {
                "id": transaction.id,
                "booking_id": transaction.booking.id,
                "booking_date": transaction.booking.booking_date.isoformat(),
                "time_slot": transaction.booking.time_slot,
                "transaction_type": transaction.transaction_type.value,
                "payment_method": transaction.payment_method.value,
                "amount": transaction.amount,
                "created_by": transaction.creator.username,
                "created_at": transaction.created_at.isoformat(),
                "updated_by": transaction.updated_by.username if transaction.updated_by else None,
                "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None
            }
        })
    except SQLAlchemyError as db_exc:
        logging.error(f"Database error in get_transaction_details: {str(db_exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Database error: {str(db_exc)}"})
    except Exception as exc:
        logging.error(f"Unexpected error in get_transaction_details: {str(exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Unexpected error: {str(exc)}"})




@router.post("/add_transaction")
async def add_transaction(
    booking_id: int = Form(...),
    transaction_type: str = Form(...),
    payment_method: str = Form(...),
    amount: float = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        booking = await db.get(Booking, booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"success": False, "message": "Booking not found"})

    # Get the slot price for this booking
        slot_price_result = await db.execute(
            select(SlotPrice)
            .filter(
                SlotPrice.time_slot == booking.time_slot,
                SlotPrice.day_of_week == DayOfWeek[booking.booking_date.strftime('%A').upper()],
                or_(
                    and_(
                        SlotPrice.start_date <= booking.booking_date,
                        SlotPrice.end_date >= booking.booking_date
                    ),
                    and_(
                        SlotPrice.start_date == None,
                        SlotPrice.end_date == None
                    )
                )
            )
            .order_by(SlotPrice.is_default.desc())
        )
        slot_prices = slot_price_result.scalars().all()

        if not slot_prices:
            return JSONResponse(status_code=404, content={
                "success": False, 
                "message": f"Slot price not found for booking (ID: {booking_id}, Date: {booking.booking_date}, Time: {booking.time_slot})"
            })

        # Use the first (most specific) slot price
        slot_price = slot_prices[0]

        transaction = Transaction(
            booking_id=booking_id,
            transaction_type=TransactionType[transaction_type],
            payment_method=PaymentMethod[payment_method],
            amount=amount,
            created_by=current_user.id,
            created_at=datetime.now(timezone.utc)
            )
        db.add(transaction)
        await db.flush()

        summary = await db.get(TransactionSummary, booking_id)
        if not summary:
            summary = TransactionSummary(booking_id=booking_id, total_price=slot_price.price)
            db.add(summary)

        transactions = await db.execute(
            select(Transaction).filter(Transaction.booking_id == booking_id)
        )
        transactions = transactions.scalars().all()

        summary.total_paid = sum(t.amount for t in transactions if t.transaction_type in [TransactionType.BOOKING_PAYMENT, TransactionType.SLOT_PAYMENT])
        summary.leftover = summary.total_price - summary.total_paid
        summary.booking_payment = sum(t.amount for t in transactions if t.transaction_type == TransactionType.BOOKING_PAYMENT)
        summary.slot_payment = sum(t.amount for t in transactions if t.transaction_type == TransactionType.SLOT_PAYMENT)
        summary.cash_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.CASH)
        summary.bkash_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.BKASH)
        
        if not summary.booking_payment_date and transaction.transaction_type == TransactionType.BOOKING_PAYMENT:
            summary.booking_payment_date = transaction.created_at.date()

        if summary.leftover == 0:
            summary.status = TransactionStatus.SUCCESSFUL
        elif summary.total_paid > 0:
            summary.status = TransactionStatus.PARTIAL
        else:
            summary.status = TransactionStatus.PENDING

        await db.commit()
        return JSONResponse(content={"success": True, "message": "Transaction added successfully"})
    
    except SQLAlchemyError as db_exc:
        await db.rollback()
        logging.error(f"Database error in add_transaction: {str(db_exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Database error: {str(db_exc)}"})
    except Exception as exc:
        logging.error(f"Unexpected error in add_transaction: {str(exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Unexpected error: {str(exc)}"})




@router.get("/transaction_summaries")
async def get_transaction_summaries(db: AsyncSession = Depends(get_db)):
    try:
        summaries = await db.execute(
            select(TransactionSummary)
            .options(joinedload(TransactionSummary.booking))
            .order_by(TransactionSummary.updated_at.desc())
            .limit(10)
        )
        
        result = []
        for summary in summaries.scalars():
            booking = summary.booking
            result.append({
                "booking_date": booking.booking_date.isoformat(),
                "slot": booking.time_slot,
                "status": summary.status.value,
                "total_paid": summary.total_paid,
                "leftover": summary.leftover,
                "booking_payment": summary.booking_payment,
                "slot_payment": summary.slot_payment,
                "cash_payment": summary.cash_payment,
                "bkash_payment": summary.bkash_payment,
                "last_payment_date": summary.updated_at.date().isoformat(),
                "booking_payment_date": summary.booking_payment_date.isoformat() if summary.booking_payment_date else None,
            })
        
        return JSONResponse(content={"success": True, "summaries": result})
    except SQLAlchemyError as e:
        logging.error(f"Database error in get_transaction_summaries: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Database error: {str(e)}"})
    except Exception as e:
        logging.error(f"Unexpected error in get_transaction_summaries: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Unexpected error: {str(e)}"})





@router.post("/update_transaction")
async def update_transaction(
    transaction_id: int = Form(...),
    transaction_type: str = Form(...),
    payment_method: str = Form(...),
    amount: float = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        transaction = await db.get(Transaction, transaction_id)
        if not transaction:
            return JSONResponse(status_code=404, content={"success": False, "message": "Transaction not found"})

        transaction.transaction_type = TransactionType[transaction_type]
        transaction.payment_method = PaymentMethod[payment_method]
        transaction.amount = amount
        transaction.updated_by = current_user.id
        transaction.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.flush()

        # Recalculate summary
        summary = await db.get(TransactionSummary, transaction.booking_id)
        if not summary:
            return JSONResponse(status_code=404, content={"success": False, "message": "Transaction summary not found"})

        transactions = await db.execute(
            select(Transaction).filter(Transaction.booking_id == transaction.booking_id)
        )
        transactions = transactions.scalars().all()

        summary.total_paid = sum(t.amount for t in transactions if t.transaction_type in [TransactionType.BOOKING_PAYMENT, TransactionType.SLOT_PAYMENT])
        summary.leftover = summary.total_price - summary.total_paid
        summary.booking_payment = sum(t.amount for t in transactions if t.transaction_type == TransactionType.BOOKING_PAYMENT)
        summary.slot_payment = sum(t.amount for t in transactions if t.transaction_type == TransactionType.SLOT_PAYMENT)
        summary.cash_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.CASH)
        summary.bkash_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.BKASH)
        summary.nagad_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.NAGAD)
        summary.card_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.CARD)
        summary.bank_transfer_payment = sum(t.amount for t in transactions if t.payment_method == PaymentMethod.BANK_TRANSFER)
        
        if summary.leftover == 0:
            summary.status = TransactionStatus.SUCCESSFUL
        elif summary.total_paid > 0:
            summary.status = TransactionStatus.PARTIAL
        else:
            summary.status = TransactionStatus.PENDING

        await db.commit()
        return JSONResponse(content={"success": True, "message": "Transaction updated successfully"})
    
    except SQLAlchemyError as db_exc:
        await db.rollback()
        logging.error(f"Database error in update_transaction: {str(db_exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Database error: {str(db_exc)}"})
    except Exception as exc:
        logging.error(f"Unexpected error in update_transaction: {str(exc)}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Unexpected error: {str(exc)}"})