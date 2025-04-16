# function/login.py

import oracledb

# Initialize thick mode by pointing to your Instant Client folder
# (Only needed once in your entire application, typically at the top-level.)
oracledb.init_oracle_client(lib_dir=r"D:\instantclient_23_6")

def authenticate(username: str, password: str):
    """
    Authenticates a user against the Oracle 'users' table
    ensuring GROUP_CODE is one of 1010, 1001, or 1005.

    Returns:
        (bool, dict or str):
           - bool  => True if user authenticated, False otherwise
           - dict  => A dictionary with user info if success
           - str   => Error message if failure
    """

    # Connection details
    # Adjust as needed for your environment
    DB_USER = "HOSPUSER"
    DB_PASSWORD = "hosp"
    DB_DSN = "128.16.7.5:1521/hosp1121"  # host:port/serviceName

    ALLOWED_GROUP_CODES = (1010, 1001, 1005)

    try:
        # Connect to Oracle DB using a context manager
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN) as connection:
            with connection.cursor() as cursor:

                # Step 1: Attempt primary authentication with consolidated query
                primary_query = """
                    SELECT USER_NAME, GROUP_CODE
                    FROM users
                    WHERE USER_NAME = :username
                    AND USER_PASSWORD = :password
                    AND GROUP_CODE IN (1010, 1001, 1005)
                """
                cursor.execute(primary_query, username=username, password=password)
                primary_row = cursor.fetchone()

                if primary_row:
                    # Authentication successful
                    user_info = {
                        "user_name": primary_row[0],
                        "group_code": primary_row[1]
                    }
                    return True, user_info
                else:
                    # Primary authentication failed; determine the specific reason

                    # Step 2: Check if username exists
                    check_username_query = """
                        SELECT GROUP_CODE
                        FROM users
                        WHERE USER_NAME = :username
                    """
                    cursor.execute(check_username_query, username=username)
                    user_row = cursor.fetchone()

                    if not user_row:
                        return False, "إسم المستخدم غير موجود"

                    stored_group_code = user_row[0]

                    # Step 3: Check if password is correct
                    check_password_query = """
                        SELECT 1
                        FROM users
                        WHERE USER_NAME = :username
                          AND USER_PASSWORD = :password
                    """
                    cursor.execute(check_password_query, username=username, password=password)
                    password_row = cursor.fetchone()

                    if not password_row:
                        return False, "كلمة المرور غير صحيحة"

                    # Step 4: Check if user is in an authorized group
                    if stored_group_code not in ALLOWED_GROUP_CODES:
                        return False, "غير مسموح للمستخدم"

                    # Fallback message (should not reach here)
                    return False, "Authentication failed due to unknown reasons."

    except oracledb.Error as e:
        # Oracle-specific error
        return False, f"Database error: {str(e)}"
    except Exception as e:
        # General error
        return False, str(e)

# Example usage:
if __name__ == "__main__":
    test_username = "testUser"
    test_password = "testPass"

    success, result = authenticate(test_username, test_password)
    if success:
        print(f"Authenticated! User Info: {result}")
    else:
        print(f"Authentication failed: {result}")
