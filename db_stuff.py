from sqlmodel import Field, SQLModel, create_engine

class Job(SQLModel, table=True):
    id: int|None = Field(default=None, primary_key=True)
    status:str

sqlite_name = "potter.db"
sqlite_url = f"sqlite:///{sqlite_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

