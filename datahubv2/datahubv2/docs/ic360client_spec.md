# IC360 Client Specification

## Overview
The IC360 Client (`IC360Client`) provides a connection interface to the IC360 PostgreSQL database. This client handles database connections, query execution, and retrieval of geographical data needed for the DataHub system.

## Configuration

Connection parameters are stored in the "DH Setting" DocType:
- **host**: Database server hostname or IP address
- **database**: Name of the IC360 database
- **username**: Database username for authentication
- **password**: Database password for authentication
- **port**: Database port (default PostgreSQL port is 5432)

## Main Features

### 1. Connection Management
The client manages database connections automatically:
- **Creating connections**: Establishes connections on demand
- **Connection pooling**: Reuses existing connections when available
- **Error handling**: Graceful error reporting for connection issues

### 2. Query Execution
Executes SQL queries with proper error handling:
- **SELECT queries**: Returns results as a list of dictionaries
- **Data manipulation**: Handles INSERT, UPDATE, DELETE with transactions
- **Error recovery**: Rolls back transactions on error

### 3. Geographical Data
Retrieves geographical location data:
- **Area information**: Gets province, amphur, and district data
- **Code mapping**: Provides codes for geographical names
- **Postal code lookup**: Retrieves postal codes for locations

## Methods

### 1. connect()
Establishes a connection to the PostgreSQL database.

**Returns**:
- `bool`: True if connection is successful, False otherwise

**Example**:
```python
client = IC360Client()
success = client.connect()
```

### 2. disconnect()
Closes the database connection.

**Example**:
```python
client = IC360Client()
# ... operations ...
client.disconnect()
```

### 3. execute_query(query, params)
Executes a SQL query with parameters.

**Parameters**:
- `query` (str): SQL query to execute
- `params` (List, optional): List of parameters for the query

**Returns**:
- `List[Dict]`: Results as a list of dictionaries for SELECT queries
- `[]`: Empty list for other query types

**Example**:
```python
client = IC360Client()
query = "SELECT * FROM customer WHERE contact_id = %s"
params = ["12345"]
results = client.execute_query(query, params)
```

### 4. get_area_info(province_name, amphur_name, district_name)
Retrieves geographical area information.

**Parameters**:
- `province_name` (str): Name of the province (จังหวัด)
- `amphur_name` (str): Name of the amphur (อำเภอ)
- `district_name` (str): Name of the district (ตำบล)

**Returns**:
- `List[Dict]`: List containing a dictionary with area information
  - `province_code`: Code for the province
  - `province_name`: Name of the province
  - `amphur_code`: Code for the amphur
  - `amphur_name`: Name of the amphur
  - `district_code`: Code for the district
  - `district_name`: Name of the district
  - `zipcode`: Postal code for the area

**Example**:
```python
client = IC360Client()
area_info = client.get_area_info(
    province_name="กรุงเทพมหานคร",
    amphur_name="ห้วยขวาง",
    district_name="ห้วยขวาง"
)
if area_info:
    area = area_info[0]
    province_code = area["province_code"]
    amphur_code = area["amphur_code"]
    district_code = area["district_code"]
    zipcode = area["zipcode"]
```

## Error Handling

The client includes comprehensive error handling:

1. **Connection errors**: Logged with error details
2. **Query errors**: 
   - SQL errors are logged
   - Transactions are rolled back
   - Exceptions are re-raised for caller handling
3. **Area lookup errors**: Logged with query parameters

## Complete Usage Example

```python
from datahub.lib.ic360.client import IC360Client

try:
    # Initialize client
    client = IC360Client()
    
    # Execute a query to get customer data
    query = """
        SELECT 
            contact_id, 
            first_name, 
            last_name, 
            mobile, 
            email 
        FROM 
            customer 
        WHERE 
            contact_id = %s
    """
    params = ["12345"]
    customer_data = client.execute_query(query, params)
    
    if customer_data:
        customer = customer_data[0]
        print(f"Customer: {customer['first_name']} {customer['last_name']}")
        
        # Get address information
        if customer.get("province_name") and customer.get("amphur_name") and customer.get("sub_district_name"):
            area_info = client.get_area_info(
                province_name=customer["province_name"],
                amphur_name=customer["amphur_name"],
                district_name=customer["sub_district_name"]
            )
            
            if area_info:
                print(f"Zipcode: {area_info[0]['zipcode']}")
                
except Exception as e:
    print(f"Error: {str(e)}")
    
finally:
    # Always disconnect
    client.disconnect()
```

## Best Practices

1. **Connection Management**:
   - Always disconnect after use, preferably in a finally block
   - Handle connection failures gracefully

2. **Query Construction**:
   - Use parameterized queries to prevent SQL injection
   - Keep queries simple and focused

3. **Error Handling**:
   - Wrap client usage in try/except blocks
   - Log errors for debugging
   - Handle potential database errors in your application logic

4. **Performance Optimization**:
   - Limit result sets to necessary data
   - Use specific columns in SELECT clauses
   - Add LIMIT clauses when appropriate

5. **Security**:
   - Never store credentials in code
   - Use the DH Setting DocType for configuration
   - Validate user input before using in queries
