def showclaims(cursor):
    print("Claims Details :")
    query = " SELECT * FROM claims"
    cursor.execute(query)
    claims=cursor.fetchall()
    for claim in claims:
        print(claim)




def add_claim(cursor,conn):
    print("==File a Claim===")
    claim_id = int(input("Enter the claim Id:"))
    policy_id = int(input("Enter the policy Id:"))
    amount = int(input("Enter the amount:"))
    status = input("Enter the status :")

    query = """INSERT INTO claims(claim_id,policy_id,amount,status) 
    VALUES(%s,%s,%s,%s)"""

    values = (claim_id,policy_id,amount,status)
    cursor.execute(query,values)
    conn.commit()
    print("claim Added Succesfully!!")