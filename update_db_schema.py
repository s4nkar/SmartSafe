import mysql.connector
from database import user, password, host, database, port

def apply_updates():
    try:
        con = mysql.connector.connect(user=user, password=password, host=host, port=port)
        cur = con.cursor()
        
        # Create DB if not exists (handling fresh install case)
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cur.execute(f"USE {database}")
        
        # 1. Rename 'users' to 'user' if 'users' exists and 'user' does not
        cur.execute("SHOW TABLES LIKE 'users'")
        if cur.fetchone():
            print("Found 'users' table. Renaming to 'user'...")
            cur.execute("RENAME TABLE `users` TO `user`")
        else:
            print("'users' table not found (might already be 'user' or not created).")
            
        # 2. Add 'voice_embedding' to 'user_biometrics'
        cur.execute("SHOW COLUMNS FROM `user_biometrics` LIKE 'voice_embedding'")
        if not cur.fetchone():
            print("Adding 'voice_embedding' column to 'user_biometrics'...")
            cur.execute("ALTER TABLE `user_biometrics` ADD COLUMN `voice_embedding` LONGBLOB")
        else:
            print("'voice_embedding' column already exists.")

        # 3. Ensure 'user' table exists (if strictly needed)
        # We rely on the app to create it if it doesn't exist via SQL init, but we fixed the SQL file.
        
        con.commit()
        cur.close()
        con.close()
        print("Database schema updated successfully.")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    apply_updates()
