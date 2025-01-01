import mysql.connector
from threading import Thread
import faker

class mysql_data:
    def __init__(self, host=None, user=None, password=None, database=None, table=None):
        self.host = host
        self.user_host = user
        self.password_host = password
        self.database = database
        self.table = table
    def connect_database(self):
        self.connect = mysql.connector.connect(host=self.host, user=self.user_host, password=self.password_host)
        self.cursor = self.connect.cursor()
       
    def create_database(self):
        # connect = mysql.connector.connect(host=self.host, user=self.user_host, password=self.password_host)
        # cursor = connect.cursor()
        self.cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.database}')
        self.cursor.execute(f'USE {self.database}')
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.table}(
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(255) NOT NULL,
            address VARCHAR(255) NOT NULL,
            expdate DATE NOT NULL,
            uuid VARCHAR(255) NOT NULL DEFAULT 0,
            inforuser VARCHAR(255),
            timesapproval VARCHAR(255),
            notes VARCHAR(255)
            )
            """)
        self.connect.commit()
        self.cursor.close()
    def create_user(self):
        fake = faker.Faker()
        username = fake.name()
        password = fake.password()
        phone = fake.phone_number()
        address = fake.address()
        expdate = fake.date()
        uuid = fake.uuid4()
        inforuser = fake.text()
        timesapproval = fake.text()
        notes = fake.text()
        # connect = mysql.connector.connect(host=self.host, user=self.user_host, password=self.password_host)
        # cursor = connect.cursor()
        self.cursor.execute(f'USE {self.database}')
        self.cursor.execute(f'INSERT INTO {self.table} (username, password, phone, address, expdate, uuid, inforuser, timesapproval, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (username, password, phone, address, expdate, uuid, inforuser, timesapproval, notes))
        self.connect.commit()
        # self.cursor.close()
    def close_database(self):
        self.connect.close()


# host = "localhost"
# user = "root"
# password = "123456"
# database_name = "user_data"
# table_name = "customers"

# sql= mysql_data(host, user, password, database_name, table_name)
# sql.connect_database()
# sql.create_database()

# for i in range(1000):
#     sql.connect_database()
#     sql.create_user()
# sql.close_database()
