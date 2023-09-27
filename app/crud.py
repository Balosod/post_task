from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# FUNCTION TO HASHED USER PASSWORD
def get_password_hash(password):
    return pwd_context.hash(password)


# GET USER BY EMAIL
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# CREATE USER
def create_user(db: Session, user: schemas.UserCreateAndGet):
    hashed_pass = get_password_hash(user.password)
    db_user = models.User(email=user.email, password=hashed_pass)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# GET ALL POSTS
def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()


# CREATE POST FOR USER
def create_user_post(db: Session, post: schemas.PostCreate, email: str):
    db_item = models.Post(**post.dict(), owner_id=email)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# GET ALL POST BY USER
def get_all_post(db: Session, email: str):
    return db.query(models.Post).filter(models.Post.owner_id == email).all()


# DELETE POST
def delete_post(db: Session, id: int, email: str):
    db_post = (
        db.query(models.Post)
        .filter(models.Post.id == id, models.Post.owner_id == email)
        .first()
    )
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False
