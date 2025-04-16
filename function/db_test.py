import oracledb
oracledb.init_oracle_client(lib_dir=r"G:\instantclient_23_6")

def check_user(username_input, password_input):
    """
    Runs a query to check if a user with (username_input, password_input)
    is in GROUP_CODE = 1011 in the 'users' table.
    """
    # 2) Connect to the remote Oracle DB
    with oracledb.connect(
        user="HOSPUSER",
        password="hosp",
        dsn="128.16.7.5:1521/hosp1121"
    ) as connection:
        # 3) Create a cursor and run your query
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT USER_NAME, GROUP_CODE
                FROM users
                WHERE USER_NAME = :username
                  AND USER_PASSWORD = :password
                  AND GROUP_CODE = 1011
                """,
                username=username_input,
                password=password_input
            )

            row = cursor.fetchone()
            if row:
                print("Login successful!")
                #print(f"User: {row[0]}, Group Code: {row[1]}")
            else:
                print("Invalid credentials or not in group 1011.")

# Example usage:
if __name__ == "__main__":
    # Replace these with real values
    username_input = "شيماء_حيدر"
    password_input = "123"
    check_user(username_input, password_input)
