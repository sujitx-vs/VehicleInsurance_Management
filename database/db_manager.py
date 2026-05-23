import mysql.connector

conn = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "3399",
    database = "insurance_db"
)

if conn.is_connected:
    print("Connection Established!!")

cursor = conn.cursor()