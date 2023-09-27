from fastapi import Depends, FastAPI, HTTPException, Request, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import crud, models, schemas
from .database import SessionLocal, engine
import cachetools
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
import json
from decouple import config

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
cache = cachetools.LRUCache(maxsize=1000)
cache_timeout = timedelta(minutes=5)


# SETTINGS FOR JWT
class Settings(BaseModel):
    authjwt_secret_key: str = config("authjwt_secret_key")
    authjwt_access_token_expires = config("authjwt_access_token_expires")
    authjwt_algorithm = config("authjwt_algorithm")


@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# VERIFY HASHED PASSWORD TO THE USER PASSWORD
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# REGISTER USER  ROUTE
@app.post(
    "/users/signup",
)
def create_user(
    user: schemas.UserCreateAndGet,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    # CHECK IF USER IS REGISTER IN DB
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_data = crud.create_user(db=db, user=user)
    access_token = Authorize.create_access_token(subject=user.email)
    refresh_token = Authorize.create_refresh_token(subject=user.email)
    return {"access_token": access_token, "refresh_token": refresh_token}


# LOGIN USER ROUTE
@app.post(
    "/users/signin",
)
def create_user(
    user: schemas.UserCreateAndGet,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    # CHECK IF USER IS REGISTER IN DB
    db_user = crud.get_user_by_email(db, email=user.email)

    # CHECK IF USER EXIST AND HASHED PASSWORD IS EQUAL TO USER PASSWORD
    if db_user and pwd_context.verify(user.password, db_user.password):
        access_token = Authorize.create_access_token(subject=db_user.email)
        refresh_token = Authorize.create_refresh_token(subject=db_user.email)
        return {"access_token": access_token, "refresh_token": refresh_token}

    return HTTPException(
        status_code=400,
        detail="User with that email doesn't exist or password incorrect",
    )


# ADD POUST ROUTE
@app.post("/addpost/")
def create_post_for_user(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    # AUTHORIZATION REQUIRED
    Authorize.jwt_required()
    print("called")

    # GET THE CURRENT USER MAKING THE REQUEST
    current_user = Authorize.get_jwt_subject()

    post = crud.create_user_post(db=db, post=post, email=current_user)
    return {"message": "post added", "data": post.id}


# GET POST ROUTE
@app.get("/getposts/")
def read_items(db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    # AUTHORIZATION REQUIRED
    Authorize.jwt_required()

    # GET THE CURRENT USER MAKING THE REQUEST
    current_user = Authorize.get_jwt_subject()

    # GET USER POST FROM CACHE
    cached_response = cache.get(current_user)

    if cached_response:
        return cached_response

    post = crud.get_all_post(db, current_user)
    expiration_time = datetime.now() + cache_timeout

    # CACHE USER POST FOR 5 MINUTES
    cache[current_user] = (post, expiration_time)
    return post


# DELETE POST ROUTE
@app.post("/deletpost/")
def delete_post(
    post: schemas.DeletePost,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    # AUTHORIZATION REQUIRED
    Authorize.jwt_required()

    # GET THE CURRENT USER MAKING THE REQUEST
    current_user = Authorize.get_jwt_subject()

    post = crud.delete_post(db, post.id, current_user)
    if post:
        return {"message": "post deleted"}

    return HTTPException(status_code=400, detail="post not found")
