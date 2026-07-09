from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.database import Base

# En lugar de ser una clase, la definimos como Tabla ya que al ser intermedia, no necesitamos consultarla (más liviano)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("users_id", Integer, ForeignKey("users.id")),
    Column("roles_id", Integer, ForeignKey("roles.id")),
)
