# ServiceNow Table Tools

This document provides an overview of the table-related tools available in the ServiceNow MCP server.

## Table of Contents
- [List Tables](#list-tables)
- [Get Records](#get-records)
- [Get Record](#get-record)
- [Get Table Schema](#get-table-schema)
- [List Table Schemas](#list-table-schemas)

## List Tables

List all available tables in the ServiceNow instance.

### Parameters
- `limit` (int, optional): Maximum number of tables to return (default: 10, max: 1000)
- `offset` (int, optional): Offset for pagination (default: 0)
- `name_filter` (str, optional): Filter tables by name
- `include_sys` (bool, optional): Include system tables (default: False)
- `include_extended` (bool, optional): Include extended tables (default: False)

### Example
```python
response = list_tables(
    config=config,
    auth_manager=auth_manager,
    params=ListTablesParams(
        limit=50,
        name_filter="incident",
        include_sys=False
    )
)
```

## Get Records

Get records from a specific table with optional filtering and pagination.

### Parameters
- `table_name` (str): Name of the table to query
- `query` (str, optional): Encoded query string for filtering records
- `fields` (List[str], optional): List of fields to include in the results
- `limit` (int, optional): Maximum number of records to return (default: 10, max: 1000)
- `offset` (int, optional): Offset for pagination (default: 0)
- `order_by` (str, optional): Field to order results by
- `order_direction` (str, optional): Sort order ("asc" or "desc", default: "desc")

### Example
```python
response = get_records(
    config=config,
    auth_manager=auth_manager,
    params=GetRecordsParams(
        table_name="incident",
        query="active=true^assigned_toISNOTEMPTY",
        fields=["number", "short_description", "state", "assigned_to"],
        limit=25,
        order_by="sys_updated_on"
    )
)
```

## Get Record

Get a single record by its sys_id.

### Parameters
- `table_name` (str): Name of the table containing the record
- `sys_id` (str): System ID of the record to retrieve
- `fields` (List[str], optional): List of fields to include in the results

### Example
```python
response = get_record(
    config=config,
    auth_manager=auth_manager,
    table_name="incident",
    sys_id="1234567890abcdef1234567890abcdef",
    fields=["number", "short_description", "description", "state"]
)
```

## Get Table Schema

Get the schema for a specific table, including field definitions.

### Parameters
- `table_name` (str): Name of the table to get the schema for
- `include_all_fields` (bool, optional): Include all fields, including system and read-only fields (default: False)

### Example
```python
response = get_table_schema(
    config=config,
    auth_manager=auth_manager,
    params=GetTableSchemaParams(
        table_name="incident",
        include_all_fields=False
    )
)
```

## List Table Schemas

List all available table schemas in the ServiceNow instance.

### Example
```python
response = list_table_schemas(
    config=config,
    auth_manager=auth_manager
)
```

## Error Handling

All functions return a response dictionary with the following structure:

```python
{
    "success": bool,           # Whether the operation was successful
    "message": str,            # Human-readable message (present if success is False)
    "error": str,             # Error details (present if success is False)
    # Additional fields specific to each function
}
```

## Best Practices

1. **Pagination**: Always use `limit` and `offset` when retrieving large numbers of records.
2. **Field Selection**: Only request the fields you need using the `fields` parameter to improve performance.
3. **Filtering**: Use the `query` parameter to filter records on the server side when possible.
4. **Error Handling**: Always check the `success` field in the response and handle errors appropriately.
5. **Rate Limiting**: Be mindful of API rate limits when making multiple requests in quick succession.
