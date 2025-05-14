import snowflake.connector
from snowflake.connector.errors import ProgrammingError
import logging

logging.basicConfig(level=logging.DEBUG)

# Snowflake connection parameters
account = 'rl25089.uk-south.azure'#'xrrunhf'
user = 'powerbi'
password = 'sqn-g94R84lFs^eN@8Y~'
warehouse = 'COMPUTE_WH'
database = 'DATA_WAREHOUSE'
schema = 'STAGING_FINANCE'

# Define your stored procedure name and any parameters it requires
stored_procedure_name = 'load_xero_json_data'
procedure_parameters = ()  # Tuple for parameters, if any

# Create a connection to Snowflake
conn = None
cursor = None
try:
    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema
    )

    # Create a cursor to interact with Snowflake
    cursor = conn.cursor()

    # Prepare the SQL call for the stored procedure
    sql = f"CALL {stored_procedure_name}({', '.join(['?'] * len(procedure_parameters))})"

    # Execute the stored procedure call with parameters
    cursor.execute(sql, procedure_parameters)

    print(f"Stored procedure {stored_procedure_name} called successfully.")

except snowflake.connector.errors.ProgrammingError as e:
    print(f"SQL error while calling stored procedure: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Clean up
    if cursor:
        cursor.close()
    if conn:
        conn.close()
