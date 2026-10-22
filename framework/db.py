"""Shared database connection for the MeshFlow framework."""
import pyodbc

SERVER = r"localhost\MSSQLSERVER02"
DATABASE = "AdventureWorks2022"


def pick_driver():
    """Use the newest installed Microsoft ODBC driver for SQL Server."""
    for name in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if name in pyodbc.drivers():
            return name
    raise RuntimeError("No ODBC Driver 17/18 for SQL Server found. Installed: "
                       + ", ".join(pyodbc.drivers()))


def connect(database=DATABASE):
    """Open a connection using Windows Authentication."""
    conn_str = (
        f"DRIVER={{{pick_driver()}}};"
        f"SERVER={SERVER};DATABASE={database};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)
