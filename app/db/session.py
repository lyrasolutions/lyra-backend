from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = "sqlite:///./lyra.db"
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from app.db.models import User, OnboardingProfile, GeneratedContent, ContentCalendar, SocialMediaAccount
    SQLModel.metadata.create_all(engine)
