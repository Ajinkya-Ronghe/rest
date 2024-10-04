import json
import re

def clean_column_name(column_name):
    # Replace special characters with underscore and convert to lowercase
    return re.sub(r'[^a-zA-Z0-9_]', '_', column_name).lower()

def clean_table_name(array_name):
    # Replace special characters in the array name with underscore and convert to lowercase
    return re.sub(r'[^a-zA-Z0-9_]', '_', array_name).lower()

def generate_sql_query_and_metadata(json_object, array_name):
    # Clean the array name for use as the table name
    cleaned_table_name = clean_table_name(array_name)
    table_name = f"esh_main.ceh_tn_{cleaned_table_name}"
    
    # Generate the primary and foreign key constraint names dynamically
    primary_key_constraint = f"{cleaned_table_name}_pkey"
    foreign_key_constraint = f"{cleaned_table_name}_fkey"
    
    # Start forming the SQL query
    sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    metadata = {"columns": []}  # Initialize the metadata structure
    
    # Get the first object from the JSON array
    first_item = json_object[0]
    
    # Add fields from the JSON object
    bank_id_included = False  # Track if "Custom Tags" field is present
    for key, value in first_item.items():
        column_name = clean_column_name(key)  # Clean the column name
        
        # Check if the value is a list or a JSON object (dict)
        if isinstance(value, (list, dict)):
            # Treat list or JSON object fields as TEXT
            data_type = "TEXT"
        else:
            # Treat scalar fields as VARCHAR
            data_type = "VARCHAR(255)"
        
        # Add column to SQL query
        sql_query += f"    {column_name} {data_type} NULL,\n"
        
        # Add to metadata, skip the auto-increment id field
        if column_name != "id":
            metadata['columns'].append({
                "column_name": column_name,
                "field_name": key,
                "data_type": data_type,
                "is_nullable": True  # Assuming all fields are nullable
            })
        
        # If "Custom Tags" field is present, mark bank_id to be included
        if key == "Custom Tags":
            bank_id_included = True
    
    # Append hardcoded fields (staging_id and id as bigserial)
    sql_query += f"""
    id bigserial NOT NULL,
    staging_id integer NULL,
    batch_id integer NULL,
    created_time timestamp without time zone NULL,
    CONSTRAINT {primary_key_constraint} PRIMARY KEY (id),
    CONSTRAINT {foreign_key_constraint} FOREIGN KEY (staging_id)
        REFERENCES esh_main.ceh_api_staging_data (id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
    );
    """
    
    # Add hardcoded columns to metadata (excluding 'id')
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
        },
        {
            "column_name": "created_time",
            "field_name": "created_time",
            "data_type": "timestamp without time zone",
            "is_nullable": True
        }
    ])
    
    # Add bank_id if "Custom Tags" field is present
    if bank_id_included:
        sql_query += "    bank_id integer NULL,\n"
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
