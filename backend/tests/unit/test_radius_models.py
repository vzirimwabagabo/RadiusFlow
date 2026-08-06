import unittest

from sqlalchemy import create_engine, insert, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from database import Base
from models import (
    NAS,
    RadAcct,
    RadCheck,
    RadGroupCheck,
    RadGroupReply,
    RadPostAuth,
    RadReply,
    RadUserGroup,
)


class RadiusModelContractTests(unittest.TestCase):
    def test_radacct_columns_match_verified_production_schema(self):
        self.assertEqual(
            set(RadAcct.__table__.columns.keys()),
            {
                "radacctid",
                "acctsessionid",
                "acctuniqueid",
                "username",
                "realm",
                "nasipaddress",
                "nasportid",
                "nasporttype",
                "acctstarttime",
                "acctupdatetime",
                "acctstoptime",
                "acctinterval",
                "acctsessiontime",
                "acctauthentic",
                "connectinfo_start",
                "connectinfo_stop",
                "acctinputoctets",
                "acctoutputoctets",
                "calledstationid",
                "callingstationid",
                "acctterminatecause",
                "servicetype",
                "framedprotocol",
                "framedipaddress",
                "framedipv6address",
                "framedipv6prefix",
                "framedinterfaceid",
                "delegatedipv6prefix",
                "class",
            },
        )
        self.assertTrue(RadAcct.__table__.c.acctuniqueid.unique)
        self.assertFalse(RadAcct.__table__.c.nasipaddress.nullable)
        self.assertTrue(RadAcct.__table__.c.acctstarttime.type.timezone)
        self.assertEqual(
            RadAcct.__table__.c.nasipaddress.type.compile(
                dialect=postgresql.dialect()
            ),
            "INET",
        )

    def test_other_radius_table_columns_and_constraints_match_schema(self):
        expected_attribute_columns = {"id", "username", "attribute", "op", "value"}
        self.assertEqual(
            set(RadCheck.__table__.columns.keys()), expected_attribute_columns
        )
        self.assertEqual(
            set(RadReply.__table__.columns.keys()), expected_attribute_columns
        )
        self.assertEqual(
            set(RadGroupCheck.__table__.columns.keys()),
            {"id", "groupname", "attribute", "op", "value"},
        )
        self.assertEqual(
            set(RadGroupReply.__table__.columns.keys()),
            {"id", "groupname", "attribute", "op", "value"},
        )
        self.assertEqual(
            set(RadUserGroup.__table__.columns.keys()),
            {"id", "username", "groupname", "priority"},
        )
        self.assertEqual(str(RadUserGroup.__table__.c.priority.server_default.arg), "0")
        self.assertFalse(NAS.__table__.c.nasname.unique)
        self.assertTrue(NAS.__table__.c.ports.nullable)

    def test_radpostauth_default_select_never_loads_pass(self):
        compiled = str(
            select(RadPostAuth).compile(dialect=postgresql.dialect())
        )

        self.assertNotIn("radpostauth.pass", compiled)
        self.assertNotIn("password", RadPostAuth.__mapper__.attrs)
        self.assertTrue(RadPostAuth.__table__.c.authdate.type.timezone)

    def test_radpostauth_pass_access_requires_explicit_model_change(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                insert(RadPostAuth.__table__).values(
                    {
                        "id": 1,
                        "username": "testuser",
                        "pass": "must-not-be-exposed",
                        "reply": "Access-Accept",
                    }
                )
            )

        with Session(engine) as session:
            row = session.scalars(select(RadPostAuth)).one()
            with self.assertRaises(InvalidRequestError):
                _ = row.pass_value

        Base.metadata.drop_all(engine)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
