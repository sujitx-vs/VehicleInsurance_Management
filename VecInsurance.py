import mysql.connector
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from database import get_db_connection

class VehicleDataError(Exception):
    pass

class BasePolicy(ABC):
    @abstractmethod
    def calculate_risk_premium(self):
        pass

class VehiclePolicy(BasePolicy):
    def __init__(self, owner, v_type, cc, year, base_value, start_date, expiry_date):
        self.owner = owner
        self.v_type = v_type
        self.cc = cc
        self.year = year
        self.base_value = base_value
        self.start_date = start_date
        self.expiry_date = expiry_date

    def calculate_risk_score(self):
        current_year = datetime.now().year
        age = current_year - self.year
        score = 0

        if age > 15: score += 45
        elif age > 8: score += 30
        elif age > 3: score += 15
        else: score += 5

        if self.cc > 2500: score += 35
        elif self.cc > 1500: score += 25
        elif self.cc > 1000: score += 10
        else: score += 5

        v_type_lower = self.v_type.lower()
        if "bike" in v_type_lower or "motorcycle" in v_type_lower: score += 20
        elif "truck" in v_type_lower or "commercial" in v_type_lower: score += 15
        elif "car" in v_type_lower: score += 5
        else: score += 10

        if self.base_value > 500000: score += 15
        elif self.base_value > 100000: score += 10
        else: score += 5

        return min(score, 100)

    def get_policy_months(self):
        days = (self.expiry_date - self.start_date).days
        return max(1, round(days / 30.44))

    def calculate_risk_premium(self):
        current_year = datetime.now().year
        age = current_year - self.year
        risk_factor = 1.2 if self.cc > 1500 else 1.0
        
        annual_premium = (self.base_value * 0.02) + (age * 500) + (risk_factor * 1000)
        
        months = self.get_policy_months()
        prorated_premium = (annual_premium / 12) * months
        
        return round(prorated_premium, 2)

class CommercialVehiclePolicy(VehiclePolicy):
    def __init__(self, owner, v_type, cc, year, base_value, start_date, expiry_date, load_capacity):
        super().__init__(owner, v_type, cc, year, base_value, start_date, expiry_date)
        self.load_capacity = load_capacity

    def calculate_risk_premium(self):
        base_premium = super().calculate_risk_premium()
        annual_load_tax = self.load_capacity * 100
        months = self.get_policy_months()
        prorated_load_tax = (annual_load_tax / 12) * months
        
        return round(base_premium + prorated_load_tax, 2)

class VehicleInsuranceManager:
    def __init__(self):
        try:
            self.conn = get_db_connection()
            self.cursor = self.conn.cursor()
            self._setup_db()
        except mysql.connector.Error as err:
            raise VehicleDataError(f"Database Error: {err}")

    def _setup_db(self):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS insurance_db")
        self.cursor.execute("USE insurance_db")

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS vehicle_policies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            owner_name VARCHAR(255),
            vehicle_type VARCHAR(50),
            engine_cc INT,
            model_year INT,
            base_value FLOAT,
            premium FLOAT,
            risk_score INT,
            is_commercial TINYINT(1),
            start_date DATE,
            expiry_date DATE)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS claims (
            id INT AUTO_INCREMENT PRIMARY KEY,
            policy_id INT,
            damage_cost FLOAT,
            incident_type VARCHAR(50),
            claim_status VARCHAR(50))''')

        self.cursor.execute("UPDATE vehicle_policies SET is_commercial = 1 WHERE is_commercial > 1")

        try:
            self.cursor.execute("ALTER TABLE vehicle_policies ADD COLUMN load_capacity FLOAT DEFAULT 0")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                pass
            else:
                raise

        self.conn.commit()

    def _get_valid_date(self, prompt_text):
        while True:
            date_str = input(prompt_text)
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("❌ Invalid format! Please enter the date exactly as YYYY-MM-DD (e.g., 2024-05-15).")

    def validate_vehicle(self, owner, cc, year, start_date, expiry_date):
        if not re.match(r"^[A-Z a-z]{3,25}$", owner):
            raise VehicleDataError("Invalid Owner Name")
        if cc < 50 or cc > 5000:
            raise VehicleDataError("Invalid Engine CC")

        current_year = datetime.now().year
        age = current_year - year

        if year < 1990 or year > current_year:
            raise VehicleDataError("Invalid Model Year")
        if age > 30:
            raise VehicleDataError("Insurance not allowed: Vehicle too old (over 30 years)")
            
        if expiry_date <= start_date:
            raise VehicleDataError("Expiry date must be after the start date!")

    def create_policy(self, owner, v_type, cc, year, value, start_date, expiry_date, is_commercial, load_capacity=None):
        self.validate_vehicle(owner, cc, year, start_date, expiry_date)

        v_type = (v_type or "").strip().capitalize()
        if is_commercial:
            if load_capacity is None:
                raise VehicleDataError("Load Capacity is required for commercial vehicles")
            policy = CommercialVehiclePolicy(owner, v_type, cc, year, value, start_date, expiry_date, load_capacity)
            comm_val = 1
        else:
            policy = VehiclePolicy(owner, v_type, cc, year, value, start_date, expiry_date)
            comm_val = 0

        risk_score = policy.calculate_risk_score()
        premium = policy.calculate_risk_premium()

        query = """
        INSERT INTO vehicle_policies
        (owner_name, vehicle_type, engine_cc, model_year, base_value, premium, risk_score, is_commercial, start_date, expiry_date, load_capacity)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        
        self.cursor.execute(query, (owner, v_type, cc, year, value, premium, risk_score, comm_val, start_date, expiry_date, load_capacity or 0))
        self.conn.commit()

        policy_id = self.cursor.lastrowid
        return {"policy_id": policy_id, "premium": premium, "risk_score": risk_score, "expires": expiry_date, "months": policy.get_policy_months()}

    def create_record(self):
        try:
            name = input("Enter Owner Name: ").capitalize()
            v_type = input("Type (Car/Bike/Truck): ").strip().capitalize()
            cc = int(input("Enter Engine CC: "))
            year = int(input("Enter Model Year: "))
            value = float(input("Enter Vehicle Market Value: "))
            
            start_date = self._get_valid_date("Enter Start Date (YYYY-MM-DD): ")
            expiry_date = self._get_valid_date("Enter Expiry Date (YYYY-MM-DD): ")
            
            is_comm = input("Commercial? (y/n): ").lower()
            is_commercial = is_comm == "y"
            load = None
            if is_commercial:
                load = float(input("Enter Load Capacity: "))

            result = self.create_policy(
                owner=name, v_type=v_type, cc=cc, year=year, value=value,
                start_date=start_date, expiry_date=expiry_date,
                is_commercial=is_commercial, load_capacity=load
            )
            print(f"✅ Policy Created | ID: {result['policy_id']} | Valid for: {result['months']} months | Premium: ${result['premium']}")

        except Exception as e:
            print(f"Error: {e}")

    def get_policies(self):
        self.cursor.execute("SELECT id, owner_name, vehicle_type, engine_cc, model_year, base_value, premium, risk_score, is_commercial, start_date, expiry_date FROM vehicle_policies")
        return self.cursor.fetchall()

    def search_policies(self, query):
        like_q = f"%{query}%"
        self.cursor.execute("SELECT id, owner_name, vehicle_type, engine_cc, model_year, base_value, premium, risk_score, is_commercial, start_date, expiry_date FROM vehicle_policies WHERE owner_name LIKE %s OR vehicle_type LIKE %s OR id LIKE %s", (like_q, like_q, like_q))
        return self.cursor.fetchall()

    def display_all(self):
        data = self.get_policies()
        print(f"\n{'ID':<4} {'Owner':<12} {'Type':<8} {'CC':<6} {'Year':<6} {'Base Value':<12} {'Premium':<10} {'Risk':<5} {'Comm':<6} {'Start':<12} {'Expires'}")
        print("-" * 105)
        for row in data:
            is_comm_str = "Yes" if row[8] >= 1 else "No"
            
            print(f"{row[0]:<4} {row[1]:<12} {row[2]:<8} {row[3]:<6} {row[4]:<6} ${row[5]:<11.2f} ${row[6]:<9.2f} {row[7]:<5} {is_comm_str:<6} {str(row[9]):<12} {row[10]}")

    def update_policy(self, pid, owner, v_type, cc, year, value, start_date, expiry_date, is_commercial, load_capacity=None):
        self.cursor.execute("SELECT owner_name, vehicle_type, engine_cc, model_year, base_value, is_commercial, start_date, expiry_date, load_capacity FROM vehicle_policies WHERE id=%s", (pid,))
        existing = self.cursor.fetchone()
        if not existing:
            raise VehicleDataError("Policy ID not found")

        ex_owner, ex_v_type, ex_cc, ex_year, ex_value, ex_is_comm, ex_start, ex_expiry, ex_load = existing
        
        owner = owner.strip() if owner and owner.strip() else ex_owner
        v_type = v_type.strip().capitalize() if v_type and v_type.strip() else ex_v_type
        cc = cc if cc is not None else ex_cc
        year = year if year is not None else ex_year
        value = value if value is not None else ex_value
        start_date = start_date if start_date is not None else ex_start
        expiry_date = expiry_date if expiry_date is not None else ex_expiry
        is_commercial = is_commercial if is_commercial is not None else bool(ex_is_comm)
        load_capacity = load_capacity if load_capacity is not None else ex_load

        self.validate_vehicle(owner, cc, year, start_date, expiry_date)

        if is_commercial:
            if load_capacity is None:
                raise VehicleDataError("Load Capacity is required for commercial vehicles")
            policy = CommercialVehiclePolicy(owner, v_type, cc, year, value, start_date, expiry_date, load_capacity)
            comm_val = 1
        else:
            policy = VehiclePolicy(owner, v_type, cc, year, value, start_date, expiry_date)
            comm_val = 0

        risk_score = policy.calculate_risk_score()
        premium = policy.calculate_risk_premium()

        query = """
        UPDATE vehicle_policies
        SET owner_name=%s, vehicle_type=%s, engine_cc=%s, model_year=%s, base_value=%s,
            premium=%s, risk_score=%s, is_commercial=%s, start_date=%s, expiry_date=%s, load_capacity=%s
        WHERE id=%s"""
        self.cursor.execute(query, (owner, v_type, cc, year, value, premium, risk_score, comm_val, start_date, expiry_date, load_capacity or 0, pid))
        self.conn.commit()

        return {"policy_id": pid, "premium": premium, "risk_score": risk_score, "months": policy.get_policy_months()}

    def update_record(self):
        try:
            pid = int(input("Enter Policy ID to update: "))
            name = input("Enter Owner Name: ").capitalize()
            v_type = input("Type (Car/Bike/Truck): ").strip().capitalize()
            cc = int(input("Enter Engine CC: "))
            year = int(input("Enter Model Year: "))
            value = float(input("Enter Vehicle Market Value: "))
            
            start_date = self._get_valid_date("Enter New Start Date (YYYY-MM-DD): ")
            expiry_date = self._get_valid_date("Enter New Expiry Date (YYYY-MM-DD): ")
            
            is_comm = input("Commercial? (y/n): ").lower()
            is_commercial = is_comm == "y"
            load = None
            if is_commercial:
                load = float(input("Enter Load Capacity: "))

            result = self.update_policy(
                pid=pid, owner=name, v_type=v_type, cc=cc, year=year, value=value,
                start_date=start_date, expiry_date=expiry_date,
                is_commercial=is_commercial, load_capacity=load
            )
            print(f"✅ Policy Updated | ID: {result['policy_id']} | Valid for: {result['months']} months | Premium: ${result['premium']}")
        except Exception as e:
            print(f"Update Error: {e}")

    def delete_policy(self, pid):
        query = "DELETE FROM vehicle_policies WHERE id=%s"
        self.cursor.execute(query, (pid,))
        self.conn.commit()
        if self.cursor.rowcount == 0:
            raise VehicleDataError("Policy ID not found")

    def delete_record(self):
        try:
            pid = int(input("Enter Policy ID to delete: "))
            self.delete_policy(pid)
            print(f"Policy Deleted | ID: {pid}")
        except Exception as e:
            print(f"Delete Error: {e}")

    def submit_claim(self, pid, damage, incident):
        self.cursor.execute("SELECT id, owner_name, vehicle_type, engine_cc, model_year, base_value, premium, risk_score, is_commercial, start_date, expiry_date FROM vehicle_policies WHERE id=%s", (pid,))
        policy = self.cursor.fetchone()
        
        if not policy:
            raise VehicleDataError("Policy not found")

        model_year = policy[4]
        base_value = policy[5]  
        risk_score = policy[7]
        expiry_date = policy[10]

        current_date = datetime.now().date()
        current_year = current_date.year
        age = current_year - model_year

        self.cursor.execute("SELECT COUNT(*) FROM claims WHERE policy_id=%s", (pid,))
        claim_count = self.cursor.fetchone()[0]

        if current_date > expiry_date:
            status = f"Rejected: Policy Expired on {expiry_date}"
        elif claim_count > 3:
            status = "Rejected: Too many claims"
        elif incident == "drunk driving":
            status = "Rejected: Illegal activity"
        elif risk_score > 75:
            status = "Rejected: High Risk"
        elif risk_score > 50:
            status = f"Partial Approved: ${round(damage * 0.6, 2)}"
        elif age > 30:
            status = "Rejected: Vehicle too old"
        elif damage > base_value:
            status = f"Partial Approved: ${round(base_value * 0.7, 2)}"
        else:
            status = f"Approved: ${round(damage, 2)}"

        query = "INSERT INTO claims (policy_id, damage_cost, incident_type, claim_status) VALUES (%s,%s,%s,%s)"
        self.cursor.execute(query, (pid, damage, incident, status))
        self.conn.commit()
        return status

    def file_claim(self):
        try:
            pid = int(input("Enter Policy ID: "))
            damage = float(input("Enter Damage Cost: "))
            incident = input("Incident Type: ").lower()

            status = self.submit_claim(pid=pid, damage=damage, incident=incident)
            print(f"Claim Result: {status}")
        except Exception as e:
            print(f"Claim Error: {e}")

    def get_claims(self):
        self.cursor.execute("SELECT * FROM claims")
        return self.cursor.fetchall()

    def search_claims(self, query):
        like_q = f"%{query}%"
        self.cursor.execute("SELECT * FROM claims WHERE policy_id LIKE %s OR incident_type LIKE %s OR claim_status LIKE %s OR id LIKE %s", (like_q, like_q, like_q, like_q))
        return self.cursor.fetchall()

    def view_claims(self):
        data = self.get_claims()
        print(f"\n{'ID':<4} {'PolicyID':<10} {'Damage':<10} {'Type':<15} {'Status'}")
        print("-" * 65)
        for row in data:
            print(f"{row[0]:<4} {row[1]:<10} ${row[2]:<9.2f} {row[3]:<15} {row[4]}")

    def get_premium_analysis(self):
        df = pd.read_sql("SELECT vehicle_type, premium FROM vehicle_policies", self.conn)
        if df.empty:
            return None
        return df.groupby("vehicle_type")["premium"].mean()

    def plot_premium_distribution(self):
        analysis = self.get_premium_analysis()
        if analysis is None or analysis.empty:
            return None

        fig, ax = plt.subplots()
        ax.pie(
            analysis.values,
            labels=analysis.index,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title("Premium Distribution by Vehicle Type")
        return fig

    def run_analysis(self):
        fig = self.plot_premium_distribution()
        if fig is None:
            print("No data available for analysis.")
            return
        plt.show()

def main_menu():
    manager = VehicleInsuranceManager()
    while True:
        print("\n=== Vehicle Insurance System ===")
        print("1. Create Policy\n2. View Policies\n3. Update Policy\n4. Delete Policy")
        print("5. Analyze Data\n6. File Claim\n7. View Claims\n8. Exit")
        c = input("Select an option: ")

        if c == '1': manager.create_record()
        elif c == '2': manager.display_all()
        elif c == '3': manager.update_record()
        elif c == '4': manager.delete_record()
        elif c == '5': manager.run_analysis()
        elif c == '6': manager.file_claim()
        elif c == '7': manager.view_claims()
        elif c == '8': 
            print("Exiting system...")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu()