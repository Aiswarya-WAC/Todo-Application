from fastapi import APIRouter, HTTPException, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from security import hash_password, verify_password, create_access_token, decode_access_token
from datetime import timedelta
from models import User, Task
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Registration Route
@router.get("/", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_user(
    request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
    
    hashed_password = hash_password(password)
    user = User(username=username, email=email, password=hashed_password)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

# Login Route
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_user(
    request: Request, response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# Dashboard Route
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    username = decode_access_token(token.split(" ")[1]) if token and "Bearer " in token else None
    if not username:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})

# Tasks Routes
@router.get("/tasks", response_model=List[dict])
def get_tasks(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    username = decode_access_token(token.split(" ")[1]) if token and "Bearer " in token else None
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.username == username).first()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    return [{"id": task.id, "name": task.name, "completed": task.completed} for task in tasks]

@router.post("/tasks")
def add_task(request: Request, taskname: str = Form(...), db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    username = decode_access_token(token.split(" ")[1]) if token and "Bearer " in token else None
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.username == username).first()
    new_task = Task(name=taskname, user_id=user.id)
    db.add(new_task)
    db.commit()
    return JSONResponse(content={"message": "Task added", "task": {"id": new_task.id, "name": new_task.name, "completed": new_task.completed}})

@router.put("/tasks/{task_id}")
def update_task(task_id: int, request: Request, taskname: str = Form(None), completed: bool = Form(None), db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    username = decode_access_token(token.split(" ")[1]) if token and "Bearer " in token else None
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if taskname is not None:
        task.name = taskname
    if completed is not None:
        task.completed = completed
    
    db.commit()
    return JSONResponse(content={"message": "Task updated", "task": {"id": task.id, "name": task.name, "completed": task.completed}})

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    username = decode_access_token(token.split(" ")[1]) if token and "Bearer " in token else None
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return JSONResponse(content={"message": "Task deleted"})

# Logout Route
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
