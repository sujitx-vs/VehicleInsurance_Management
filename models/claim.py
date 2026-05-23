
def create_claims_table(cursor):
    query = """CREATE TABLE IF NOT EXISTS  claims (
    claim_id int primary key,
    policy_id int,
    amount float,
    max_coverage float,
    status varchar(30),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
    )"""
    cursor.execute(query)
class NegativeError(Exception):
    pass
class Claim:
    def __init__(self,policy_id,amount,max_coverage):
        if amount <=0:
            raise NegativeError("Amount must be Positive")
        if amount > max_coverage:
            raise ValueError("Claim amount cannot exceed policy coverage")
        self.policy_id = policy_id
        self.amount = amount
        self.max_coverage=max_coverage
        self.status = "pending"
    @staticmethod
    def file_claim(cursor,conn):
        policy_id = int(input("enter the policy id:"))
        cursor.execute("SELECT max_coverage FROM policies WHERE policy_id = %s",(policy_id,))
        max=cursor.fetchone()
        if not max:
            print("Policy Not found!!")
            return
        amount = float(input("Enter the amount:"))
        max_coverage=max[0]
        if amount>max_coverage:
            raise ValueError("Claim amount cannot exceed policy coverage")
        claim = Claim(policy_id,amount,max_coverage)
        query = "INSERT INTO claims(policy_id, amount, max_coverage, status) VALUES (%s, %s, %s, %s)"
        values = (claim.policy_id, claim.amount, claim.max_coverage, claim.status)
        cursor.execute(query, values)
        conn.commit()
        print("Claim filed successfully! Status: Pending")