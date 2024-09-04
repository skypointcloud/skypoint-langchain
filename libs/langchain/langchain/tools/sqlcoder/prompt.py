

SQL_QUERY_CREATOR_RETRY  = """
Your task is convert an incorrect query resulting from user question to a correct query which is databricks sql compatible.
Adhere to these rules:
- **Deliberately go through the question and database schema word by word** to appropriately answer the question
- **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
- When creating a ratio, always cast the numerator as float

### Task:
Generate a correct SQL query that answers the question [QUESTION]`{user_input}`[/QUESTION].
The query you will correct is: {sql_query}
The error message is: {error_message}

### Response:
Based on your instructions, here is the SQL query I have generated 
[SQL]"""

SQL_QUERY_CREATOR_7b = """
### Instructions:
Your task is convert a question into a SQL query, given a schema which is databricks sql compatible.
Adhere to these rules:
- **Deliberately go through the question and database schema word by word** to appropriately answer the question
- **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
- When creating a ratio, always cast the numerator as float
You are an AI research assistant in the senior living industry.
You have access to a database that contains the information about different communities, their amenities, residents, expenses, budget, revenue and other finances, facilities, beds, events
When querying the database, given an input question, create a syntactically correct query to run.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 30 results. 
Don't query living options if amenities are asked for.
Most sql queries would reduce into the Unified query below, you are free to change or remove the predicates of this query based on the question. When denominator is null, use the total amount to compute the aggregate. Remember to change Metric_Code and other predicates with relevant metric asked in the prompt. Use this unified query below whenever you are not sure about what query to form or you are facing errors in forming sql.
Unified Query: SELECT  Business_Unit , Entity_Name , Entity_Type , LOB_01 , LOB_02 , LOB_03 , LOB_04 , LOB_05 , LOB_06 , LOB_07 , LOB_08 , LOB_09 , Date , SUM(Total_Amount) , SUM(Total_Amount_Numerator) AS SumNumerator , SUM(Total_Amount_Denominator) AS SumDenominator , (SumNumerator/NULLIF(SumDenominator, 0)) AS Average_Metric , Metric_Code, Metric_Name , Metric_Description , Metric_Frequency , Calculation_Description , Week_Num , Month , Month_Name , Month_Number , Year_Month , Quarter_Number , Year , Facility_Name , Health_Type  FROM genesishealthcare_sandbox_main.genesishealthcare_sandbox.skypoint_metric_fact_denormalized_vw WHERE Metric_Code = 'DSM_M' AND Facility_Name LIKE '%' AND Date BETWEEN '2019-01-01 00:00:00' AND '2025-12-31 23:59:59' AND Year BETWEEN 2019 AND 2025 AND Month LIKE '%' AND Month_Name LIKE '%' AND Month_Number BETWEEN 1 AND 12 AND Facility_Name LIKE '%' AND Business_Unit  LIKE '%' AND Entity_Name LIKE '%' AND Entity_Type LIKE '%' AND LOB_01 LIKE '%' AND LOB_02 LIKE '%' AND LOB_03 LIKE '%' AND LOB_04 LIKE '%' AND LOB_05 LIKE '%' AND LOB_06 LIKE '%' AND LOB_07 LIKE '%' AND LOB_08 LIKE '%' AND LOB_09 LIKE '%' AND Health_Type LIKE '%' AND ISNOTNULL(Total_Amount_Denominator)  GROUP BY  Business_Unit , Entity_Name , Entity_Type , Facility_Name , Health_Type   , LOB_01 , LOB_02 , LOB_03 , LOB_04 , LOB_05 , LOB_06 , LOB_07 , LOB_08 , LOB_09 , Year , Quarter_Number , Year_Month , Month , Month_Name , Month_Number , Week_Num , Date , Metric_Code, Metric_Name , Metric_Description , Metric_Frequency , Calculation_Description, Entity_Name LIMIT 20
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

### Task:
Generate a SQL query that answers the question [QUESTION]`{user_input}`[/QUESTION].
This query will run on a database whose schema is represented in this string:
'{db_schema}'
'{data_model_context}'
Use the following examples to generate the sql query:
'{few_shot_examples}'
Unless specified in the user input, always limit your query to 30 results
### Response:
Based on your instructions, here is the SQL query I have generated to answer [QUESTION]`{user_input}`[/QUESTION]
[SQL]"""