"""SQLAlchemy mappings for the verified FreeRADIUS PostgreSQL schema.

The FreeRADIUS tables are externally owned. Alembic must not create or alter
them; these models only describe the schema captured in
``radiusflow-dashboard-schema.sql``.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import deferred

from database import Base


def _inet_type():
    """Use PostgreSQL INET in production while retaining SQLite test support."""
    return Text().with_variant(INET(), "postgresql")


class RadCheck(Base):
    __tablename__ = "radcheck"
    __table_args__ = (
        Index("radcheck_username", "username", "attribute"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, server_default=text("''"))
    attribute = Column(Text, nullable=False, server_default=text("''"))
    op = Column(String(2), nullable=False, server_default=text("'=='"))
    value = Column(Text, nullable=False, server_default=text("''"))


class RadReply(Base):
    __tablename__ = "radreply"
    __table_args__ = (
        Index("radreply_username", "username", "attribute"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, server_default=text("''"))
    attribute = Column(Text, nullable=False, server_default=text("''"))
    op = Column(String(2), nullable=False, server_default=text("'='"))
    value = Column(Text, nullable=False, server_default=text("''"))


class RadUserGroup(Base):
    __tablename__ = "radusergroup"
    __table_args__ = (
        Index("radusergroup_username", "username"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, server_default=text("''"))
    groupname = Column(Text, nullable=False, server_default=text("''"))
    priority = Column(Integer, nullable=False, server_default=text("0"), default=0)


class RadGroupCheck(Base):
    __tablename__ = "radgroupcheck"
    __table_args__ = (
        Index("radgroupcheck_groupname", "groupname", "attribute"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    groupname = Column(Text, nullable=False, server_default=text("''"))
    attribute = Column(Text, nullable=False, server_default=text("''"))
    op = Column(String(2), nullable=False, server_default=text("'=='"))
    value = Column(Text, nullable=False, server_default=text("''"))


class RadGroupReply(Base):
    __tablename__ = "radgroupreply"
    __table_args__ = (
        Index("radgroupreply_groupname", "groupname", "attribute"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    groupname = Column(Text, nullable=False, server_default=text("''"))
    attribute = Column(Text, nullable=False, server_default=text("''"))
    op = Column(String(2), nullable=False, server_default=text("'='"))
    value = Column(Text, nullable=False, server_default=text("''"))


class NAS(Base):
    __tablename__ = "nas"
    __table_args__ = (
        Index("nas_nasname", "nasname"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    nasname = Column(Text, nullable=False)
    shortname = Column(Text, nullable=False)
    type = Column(
        Text,
        nullable=False,
        server_default=text("'other'"),
        default="other",
    )
    ports = Column(Integer, nullable=True)
    secret = Column(Text, nullable=False)
    server = Column(Text, nullable=True)
    community = Column(Text, nullable=True)
    description = Column(Text, nullable=True)


class RadAcct(Base):
    __tablename__ = "radacct"
    __table_args__ = (
        Index(
            "radacct_active_session_idx",
            "acctuniqueid",
            postgresql_where=text("acctstoptime IS NULL"),
        ),
        Index(
            "radacct_bulk_close",
            "nasipaddress",
            "acctstarttime",
            postgresql_where=text("acctstoptime IS NULL"),
        ),
        Index("radacct_calss_idx", "class"),
        Index("radacct_start_user_idx", "acctstarttime", "username"),
    )

    radacctid = Column(BigInteger, primary_key=True, autoincrement=True)
    acctsessionid = Column(Text, nullable=False)
    acctuniqueid = Column(Text, nullable=False, unique=True)
    username = Column(Text, nullable=True)
    realm = Column(Text, nullable=True)
    nasipaddress = Column(_inet_type(), nullable=False)
    nasportid = Column(Text, nullable=True)
    nasporttype = Column(Text, nullable=True)
    acctstarttime = Column(DateTime(timezone=True), nullable=True)
    acctupdatetime = Column(DateTime(timezone=True), nullable=True)
    acctstoptime = Column(DateTime(timezone=True), nullable=True)
    acctinterval = Column(BigInteger, nullable=True)
    acctsessiontime = Column(BigInteger, nullable=True)
    acctauthentic = Column(Text, nullable=True)
    connectinfo_start = Column(Text, nullable=True)
    connectinfo_stop = Column(Text, nullable=True)
    acctinputoctets = Column(BigInteger, nullable=True)
    acctoutputoctets = Column(BigInteger, nullable=True)
    calledstationid = Column(Text, nullable=True)
    callingstationid = Column(Text, nullable=True)
    acctterminatecause = Column(Text, nullable=True)
    servicetype = Column(Text, nullable=True)
    framedprotocol = Column(Text, nullable=True)
    framedipaddress = Column(_inet_type(), nullable=True)
    framedipv6address = Column(_inet_type(), nullable=True)
    framedipv6prefix = Column(_inet_type(), nullable=True)
    framedinterfaceid = Column(Text, nullable=True)
    delegatedipv6prefix = Column(_inet_type(), nullable=True)
    class_ = Column("class", Text, nullable=True)


class RadPostAuth(Base):
    __tablename__ = "radpostauth"
    __table_args__ = (
        Index("radpostauth_class_idx", "class"),
        Index("radpostauth_username_idx", "username"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    pass_value = deferred(Column("pass", Text, nullable=True), raiseload=True)
    reply = Column(Text, nullable=True)
    calledstationid = Column(Text, nullable=True)
    callingstationid = Column(Text, nullable=True)
    authdate = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    class_ = Column("class", Text, nullable=True)
