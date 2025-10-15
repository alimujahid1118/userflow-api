from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, registry

engine = create_engine(
    "postgresql+psycopg2://postgres:root@localhost:5432/test", echo= True
)

Sessionlocal = sessionmaker(autocommit= False, autoflush= False, bind= engine)

mapper_registry = registry()

Base = mapper_registry.generate_base()

Base.metadata.create_all(engine)