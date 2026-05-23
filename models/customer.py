
def create_customer_table(cursor):
    query = """CREATE TABLE IF NOT EXISTS customers(
    customer_id int primary key,
    name varchar(30),
    age int,
    contact varchar(10)
    )"""
    cursor.execute(query)


class InvalidAge(Exception):
    pass
class Customer():
    def __init__(self,customer_id,name,age,contact):
        if age<18:
            raise InvalidAge("Age should be 18+")
        else:
            self.customer_id = customer_id
            self.name = name
            self.age = age
            self.contact =contact
