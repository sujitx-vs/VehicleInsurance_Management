from models.customer import Customer
from models.customer import InvalidAge
def showcustomers(cursor):
    print("Customer Details :")
    query = " SELECT * FROM customers"
    cursor.execute(query)
    customers=cursor.fetchall()
    for customer in customers:
        print(customer)


def add_customer(cursor,conn):
    print("Customer registration!!")

    customer_id = int(input("Enter the customer Id:"))
    name = input("Enter the name :")
    age = int(input("Enter the age:"))
    contact = input("Enter the phone number:")
    try:
        c= Customer(customer_id,name,age,contact)
    
        query = """INSERT INTO customers(customer_id,name,age,contact) 
        VALUES(%s,%s,%s,%s)"""

        values = (c.customer_id,c.name,c.age,c.contact)
        cursor.execute(query,values)
        conn.commit()
        print("Customer Added Succesfully!!")
    except InvalidAge as e:
        print(e)

    except Exception as e:
        print("ERROR : ",e)
    

def edit_customer(cursor,conn):
    customer_id = int(input("Enter the Customer Id:"))
    query = " SELECT * FROM customers WHERE customer_id =%s"
    cursor.execute(query,(customer_id,))
    customers=cursor.fetchone()
    
    if customers :
        name = input("Enter the name :")
        age = int(input("Enter the age:"))
        contact = input("Enter the phone number:")
        try:
            c = Customer(customer_id,name,age,contact)
        except InvalidAge as e:
                print(e)
        else:
            query = """UPDATE customers SET
            name =%s,
            age = %s,
            contact = %s
            WHERE customer_id = %s
            """

            values=(c.name,c.age,c.contact,c.customer_id)

            cursor.execute(query,values)
            conn.commit()
    else:
        print("Id not found!!")

        
def delete_customer(cursor,conn):
    customer_id = int(input("Enter the Customer Id:"))
    query = "SELECT * FROM customers WHERE customer_id = %s"
    cursor.execute(query,(customer_id,))
    customer = cursor.fetchone()
    if customer:
        query = "DELETE FROM customers WHERE customer_id =%s "
        values = (customer_id,)
        cursor.execute(query,values)
        conn.commit()
        print(f"Data at id {customer_id} is deleted Successfully!! ")
    else:
        print("Id not found")