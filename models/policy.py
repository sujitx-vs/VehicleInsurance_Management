def create_policies_table(cursor):
    query = """
    CREATE TABLE IF NOT EXISTS  policies (
    policy_id int auto_increment primary key,
    customer_id int,
    type varchar(20),
    premium int, 
    coverage int,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )"""
    cursor.execute(query)

class Policy:
    def calculate_premium(self):
        if self.policy_type=="life":
            return self.coverage*0.05
        elif self.policy_type=="health":
            return self.coverage*0.04
        elif self.policy_type=="vehicle":
            return self.coverage*0.03
        else:
            raise ValueError("Invalid policy type")
    def __init__(self,customer_id,policy_type,coverage):
        self.customer_id = customer_id
        if policy_type.lower() not in ["life", "health", "vehicle"]:
            raise ValueError("Invalid policy type")
        self.policy_type = policy_type.lower()
        if coverage<=0:
                raise ValueError("Coverage must be positive")
        self.coverage = coverage
        self.premium = self.calculate_premium()
