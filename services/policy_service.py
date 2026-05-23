from models.policy import Policy
def add_policy(cursor,conn):
    print("New Policy Registration")
    customer_id = int(input("Enter the customer Id:"))
    query = """
    SELECT * FROM customers WHERE customer_id = %s
    """
    cursor.execute(query,(customer_id,))
    customer = cursor.fetchone()
    if not customer:
        print("Id not found, Cannot create policy with out customer")
        return
    pindex =int(input("Select Policy type [1.Life \n2.health\n3.Vehicle]:"))
    if pindex==1:
        policy_type = "life"
    elif pindex ==2:
        policy_type ="health"
    elif pindex ==3:
        policy_type ="vehicle"
    else:
        print("Enter the correct value!!")
        return
    try:
        coverage = int(input("Enter the coverage amount: "))
        if coverage<=0:
            raise ValueError
    except ValueError:
        print("Coverage must be positive")
        return
    
    try:
        policy = Policy(customer_id,policy_type,coverage)
    except ValueError as e:
        print("ERROR : ",e)
        return

    query = """INSERT INTO policies(customer_id,type,premium,coverage) 
    VALUES(%s,%s,%s,%s)"""

    values = (policy.customer_id,policy.policy_type,policy.premium,policy.coverage)
    cursor.execute(query,values)
    conn.commit()
    print("Policy Added Succesfully!!")


def showpolicies(cursor):
    print("Policies Details :")
    query = " SELECT * FROM policies"
    cursor.execute(query)
    policies=cursor.fetchall()
    for policy in policies:
        print(policy)
