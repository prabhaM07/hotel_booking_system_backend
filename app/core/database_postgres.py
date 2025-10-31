from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings


settings = get_settings()

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from app.models.role import Role
    
    
    print("Starting database initialization...")
    Base.metadata.create_all(bind=engine)
    print("Created all tables")

    db = SessionLocal()
    try:
        print("Creating default roles...")
        default_role_names = ["admin", "user", "staff"]
        for role_name in default_role_names:
            # Query for existence
            exists = db.query(Role).filter_by(role_name=role_name).first()
            if not exists:
                db.add(Role(role_name=role_name))
                print(f"✓ Added role: {role_name}")
            else:
                print(f"✓ Role already exists: {role_name}")
        db.commit()

        # Display roles
        roles_count = db.query(Role).count()
        print(f"✓ Total roles in database: {roles_count}")
        all_roles = db.query(Role).all()
        for role in all_roles:
            print(f"  - Role: {role.role_name} (ID: {role.id})")

    except Exception as e:
        print(f"✗ Error creating default roles: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
       
        
        