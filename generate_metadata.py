import json
import re
from datetime import datetime

def clean_column_name(column_name):
    # Strip leading/trailing spaces, replace multiple spaces or special characters with a single underscore, and convert to lowercase
    column_name = column_name.strip()
    return re.sub(r'[^a-zA-Z0-9]+', '_', column_name).lower()

def clean_table_name(table_name):
    # Replace multiple special characters and hyphens with a single underscore and convert to lowercase
    return re.sub(r'[^a-zA-Z0-9]+', '_', table_name).lower()

def infer_data_type(value):
    # Determine the data type based on the content of the value
    if isinstance(value, bool):
        return "BOOLEAN"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "FLOAT"
    elif isinstance(value, str):
        # Check for date and datetime formats
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return "DATE"
        except ValueError:
            pass
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return "TIMESTAMP"
        except ValueError:
            pass
        # Use VARCHAR with intelligent length
        if len(value) <= 50:
            return "VARCHAR(50)"
        else:
            return "VARCHAR(255)"
    else:
        return "TEXT"  # Default to TEXT for unrecognized types

def process_nested_json(nested_json, parent_key=""):
    # Process nested JSON to create column details for table schema and metadata
    nested_columns = []
    for key, value in nested_json.items():
        column_name = clean_column_name(f"{parent_key}_{key}" if parent_key else key)
        if isinstance(value, dict):
            # Recursively process nested JSON objects
            nested_columns.extend(process_nested_json(value, parent_key=column_name))
        else:
            # Infer the data type based on the content
            data_type = infer_data_type(value)
            nested_columns.append({
                "column_name": column_name,
                "field_name": key,
                "data_type": data_type,
                "is_nullable": True
            })
    return nested_columns

def generate_sql_query_and_metadata(json_object, array_name):
    # Clean the array name for use as the table name
    cleaned_table_name = clean_table_name(array_name)
    table_name = f"esh_main.ceh_tn_{cleaned_table_name}"
    
    # Determine the name for the primary key column based on whether 'id' exists in the JSON
    primary_key_name = "primary_id" if "id" in json_object[0] else "id"
    
    # Generate the primary and foreign key constraint names dynamically
    primary_key_constraint = f"{cleaned_table_name}_pkey"
    foreign_key_constraint = f"{cleaned_table_name}_fkey"
    
    # Start forming the SQL query with a commented line for dropping the table
    sql_query = f"-- DROP TABLE IF EXISTS {table_name};\n"
    sql_query += f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    # Add the primary key field as the first column, naming it based on the presence of 'id' in the JSON
    sql_query += f"    {primary_key_name} bigserial NOT NULL,\n"
    
    metadata = {"columns": []}  # Initialize the metadata structure
    
    # Get the first object from the JSON array
    first_item = json_object[0]
    
    # Add fields from the JSON object
    bank_id_included = False  # Track if "Custom Tags" field is present
    for key, value in first_item.items():
        column_name = clean_column_name(key)  # Clean the column name
        
        # Check if the value is a list or dictionary (to process nested fields)
        if isinstance(value, list) and value:
            # Process nested fields within the list and add them to the SQL and metadata
            nested_columns = process_nested_json(value[0], parent_key=column_name)
            for nested_column in nested_columns:
                sql_query += f"    {nested_column['column_name']} {nested_column['data_type']} NULL,\n"
                metadata["columns"].append(nested_column)
        
        elif isinstance(value, dict):
            # Process nested fields within the dictionary and add them to the SQL and metadata
            nested_columns = process_nested_json(value, parent_key=column_name)
            for nested_column in nested_columns:
                sql_query += f"    {nested_column['column_name']} {nested_column['data_type']} NULL,\n"
                metadata["columns"].append(nested_column)
        
        else:
            # Infer the data type based on the content
            data_type = infer_data_type(value)
            sql_query += f"    {column_name} {data_type} NULL,\n"
            metadata["columns"].append({
                "column_name": column_name,
                "field_name": key,
                "data_type": data_type,
                "is_nullable": True
            })
        
        # If "Custom Tags" field is present, mark bank_id to be included
        if key == "Custom Tags":
            bank_id_included = True
    
    # Append hardcoded fields (staging_id and created_time)
    sql_query += f"""
    staging_id integer NULL,
    batch_id integer NULL,
    created_time timestamp without time zone NULL,
    """
    
    # Add bank_id if "Custom Tags" field is present
    if bank_id_included:
        sql_query += "    bank_id integer NULL,\n"

    # Finalize the table definition with primary and foreign key constraints
    sql_query += f"""
    CONSTRAINT {primary_key_constraint} PRIMARY KEY ({primary_key_name}),
    CONSTRAINT {foreign_key_constraint} FOREIGN KEY (staging_id)
        REFERENCES esh_main.ceh_api_staging_data (id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
    );
    """
    
    # Add hardcoded columns to metadata (including 'staging_id' but excluding 'id' and 'created_time')
    metadata['columns'].extend([
        {
            "column_name": "staging_id",
            "field_name": "staging_id",
            "data_type": "integer",
            "is_nullable": True
        },
        {
            "column_name": "batch_id",
            "field_name": "batch_id",
            "data_type": "integer",
            "is_nullable": True
        }
    ])
    
    # Add bank_id to metadata if it's included
    if bank_id_included:
        metadata['columns'].append({
            "column_name": "bank_id",
            "field_name": "bank_id",
            "data_type": "integer",
            "is_nullable": True
        })
    
    return sql_query, metadata, table_name

def generate_insert_query(array_name, metadata, table_name, json_question_template):
    insert_query = f"""
    INSERT INTO esh_main.ceh_api_json_metadata_type(
        name, json_metadata, table_name, json_question_template
    )
    VALUES (
        '{array_name}', 
        '{json.dumps(metadata)}', 
        '{table_name}', 
        '{json.dumps(json_question_template)}'
    );
    """
    return insert_query

def process_json_file(input_file, output_file):
    # Read the JSON object from the input file
    with open(input_file, 'r') as file:
        json_object = json.load(file)
    
    # Get the array name from the JSON object (dynamically)
    array_name = next(iter(json_object))
    
    # Generate the SQL query, metadata, and table name using the dynamic table name
    sql_query, metadata, table_name = generate_sql_query_and_metadata(json_object[array_name], array_name)
    
    # Generate the insert query
    insert_query = generate_insert_query(array_name, metadata, table_name, json_object)
    
    # Write the SQL transaction to the output file
    with open(output_file, 'w') as file:
        file.write("START TRANSACTION;\n")  # Start the transaction
        file.write(sql_query)
        file.write("\n")
        file.write(insert_query)
        file.write("\nCOMMIT;\n")  # Commit the transaction

if __name__ == "__main__":
    # Define input and output file paths
    input_file = 'input.json'  # Input JSON file
    output_file = 'output_sql.sql'  # Output SQL transaction file
    
    # Process the JSON and generate SQL transaction
    process_json_file(input_file, output_file)
