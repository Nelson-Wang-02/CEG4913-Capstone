#quick script to create database.
import mysql.connector
db = mysql.connector.connect(
    host = "localhost", 
    user = "tony",  #Please put username
    password = "Aliame123",  #Please put your password
)

cursor = db.cursor()
#run this script once, upon running it. Comment the line below!
#cursor.execute("CREATE DATABASE dumbbellDore") #DONT UNCOMMENT THIS LINE, WILL CREATE DB AGAIN, MAY WIPE DATA. 

#verification
cursor.execute("SHOW DATABASES")
for database in cursor:
    print(database)