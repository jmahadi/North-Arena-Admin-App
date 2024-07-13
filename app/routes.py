from fastapi import APIRouter, Depends, Request, Form, HTTPException , Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from sqlalchemy.orm import joinedload
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime , timedelta  ,timezone
from dateutil.relativedelta import relativedelta
from .database import SessionLocal
from .models import User , Booking
from .auth import create_access_token, get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_db():
    async with SessionLocal() as session:
        yield session

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



@router.get("/transactions", response_class=HTMLResponse)
async def transactions(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "current_user": current_user
    })





@router.post("/add_column", response_class=HTMLResponse)
async def add_column(request: Request, table_name: str = Form(...), column_name: str = Form(...), column_type: str = Form(...), db: AsyncSession = Depends(get_db)):
    await db.execute(text(f'ALTER TABLE public.{table_name} ADD COLUMN {column_name} {column_type}'))
    await db.commit()
    return "Column added"

@router.get("/add_column", response_class=HTMLResponse)
async def add_column_get(request: Request):
    return templates.TemplateResponse("add_column.html", {"request": request})

@router.post("/drop_column", response_class=HTMLResponse)
async def drop_column(request: Request, table_name: str = Form(...), column_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    await db.execute(text(f'ALTER TABLE public.{table_name} DROP COLUMN {column_name}'))
    await db.commit()
    return f'Column {column_name} dropped from table {table_name}'

@router.get("/drop_column", response_class=HTMLResponse)
async def drop_column_get(request: Request):
    return templates.TemplateResponse("drop_column.html", {"request": request})

@router.post("/insert_user", response_class=HTMLResponse)
async def insert_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    user = User(username=username, email=email)
    user.set_password(password)
    db.add(user)
    await db.commit()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/insert_user", response_class=HTMLResponse)
async def insert_user_get(request: Request):
    return templates.TemplateResponse("insert_user.html", {"request": request})
