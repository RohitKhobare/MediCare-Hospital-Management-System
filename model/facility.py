from .person import Person

# Facility Class


class Facility:
    def __init__(self, name, facility_type, premium, description, cost, facility_id=None):
        self.facility_id = facility_id
        self.name = name
        self.type = facility_type
        self.premium = premium
        self.description = description
        self.cost = cost

    def save_to_db(self, cursor, conn):
        query = "INSERT INTO facilities (name, type, premium, description, cost) VALUES (?, ?, ?, ?, ?)"
        values = (self.name, self.type, self.premium, self.description, self.cost)
        cursor.execute(query, values)
        conn.commit()

    @staticmethod
    def get_all(cursor):
        cursor.execute("SELECT * FROM facilities")
        return cursor.fetchall()

    @staticmethod
    def delete_from_db(cursor, conn, facility_id):
        cursor.execute("DELETE FROM facilities WHERE facility_id = ?", (facility_id,))
        conn.commit()