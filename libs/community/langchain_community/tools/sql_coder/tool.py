# flake8: noqa
"""Tools for interacting with a SQL database."""
from typing import Any, Dict, List, Optional
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_coder.prompt import SQL_QUERY_CREATOR_RETRY
from langchain_core.pydantic_v1 import BaseModel, Extra, Field
from langchain_core.tools import StateTool
import re

ERROR = ""
class BaseSQLDatabaseTool(BaseModel):
    """Base tool for interacting with a SQL database."""

    db: SQLDatabase = Field(exclude=True)

    # Override BaseTool.Config to appease mypy
    # See https://github.com/pydantic/pydantic/issues/4173
    class Config(StateTool.Config):

        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.allow

  
class QuerySparkSQLDataBaseTool(StateTool):
    """Tool for querying a SQL database."""

    class Config(StateTool.Config):
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.allow

    db: SQLDatabase = Field(exclude=True)
    name: str = "sql_db_query"
    description: str = """
    Input to this tool is a detailed and correct SQL query, output is a result from the database.
    If the query is not correct, an error message will be returned.
    If an error is returned, re-run the retry_sql_db_query_creator tool to get the correct query.
    """

    def __init__(__pydantic_self__, **data: Any) -> None:
        """Initialize the tool."""
        super().__init__(**data)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""
        if not hasattr(self, "state"):
            return "This tool is not meant to be run directly. Start with a SQLQueryCreatorTool"
        executable_query = (
            extracted_sql_query.strip()
            if (extracted_sql_query := self._extract_sql_query())
            else query.strip()
        )
        executable_query = executable_query.strip('\"')
        executable_query = re.sub('\\n```', '',executable_query)
        self.db.run_no_throw(executable_query)
        return self.db.run_no_throw(executable_query, include_columns=True)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("QuerySparkSQLDataBaseTool does not support async")

    def _extract_sql_query(self):
        for value in reversed(self.state):
            for key, input_string in value.items():
                if "tool='retry_sql_db_query_creator'" in key:
                    return input_string
                elif "tool='sql_db_query_creator'" in key:
                    return input_string
        return None
    


class RetrySqlQueryCreatorTool(StateTool):
    """Tool for re-creating SQL query.Use this to retry creation of sql query."""

    name = "retry_sql_db_query_creator"
    description = """
    This is a tool used to re-create sql query for user input based on the incorrect query generated and error returned from sql_db_query tool.
    Input to this tool is user prompt, incorrect sql query and error message
    Output is a sql query
    After running this tool, you can run sql_db_query tool to get the result
    """
    sqlcreatorllm: BaseLanguageModel = Field(exclude=True) 
    

    class Config(StateTool.Config):
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.allow

    def __init__(__pydantic_self__, **data: Any) -> None:
        """Initialize the tool."""
        super().__init__(**data)

    def _run(
        self,
        user_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the SQL query for the incorrect query."""
        return self._create_sql_query(user_input)

    async def _arun(
        self,
        table_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("SqlQueryCreatorTool does not support async")

    def _create_sql_query(self,user_input):
        
        sql_query = self._extract_sql_query()
        error_message = self._extract_error_message()
        if sql_query is None:
            return "This tool is not meant to be run directly. Start with a SQLQueryCreatorTool"
        
        prompt_input = PromptTemplate(
            input_variables=["user_input","sql_query", "error_message"],
            template=SQL_QUERY_CREATOR_RETRY
        )
        query_creator_chain = LLMChain(llm=self.sqlcreatorllm, prompt=prompt_input)

        sql_query = query_creator_chain.run(
                    (
                        {
                            "sql_query": sql_query,
                            "error_message": error_message,
                            "user_input": user_input
                        }
                    )
                )
        sql_query = sql_query.replace("```","")
        sql_query = sql_query.replace("sql","")
        
        return sql_query
    
    def _extract_sql_query(self):
        for value in reversed(self.state):
            for key, input_string in value.items():
                if "tool='retry_sql_db_query_creator'" in key:
                    return input_string
                elif "tool='sql_db_query_creator'" in key:
                    return input_string
        return None

    def _extract_error_message(self):
        for value in reversed(self.state):
            for key, input_string in value.items():
                if "tool='sql_db_query'" in key:
                    if "Error" in input_string:
                        return input_string
        return None
    
class SqlQueryCreatorTool(StateTool):
    """Tool for creating SQL query.Use this to create sql query."""

    name = "sql_db_query_creator"
    description = """
    This is a tool used to create sql query for user input based on the schema of the table and few_shot_examples.
    Input to this tool is input prompt and table schema and few_shot_examples
    Output is a sql query
    """
    sqlcreatorllm: BaseLanguageModel = Field(exclude=True) 
    SQL_QUERY_CREATOR_TEMPLATE: str 

    class Config(StateTool.Config):
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.allow

    def __init__(__pydantic_self__, **data: Any) -> None:
        """Initialize the tool."""
        super().__init__(**data)

    def _run(
        self,
        user_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the SQL query for the user input."""
        return self._create_sql_query(user_input)

    async def _arun(
        self,
        table_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("SqlQueryCreatorTool does not support async")

    def _parse_few_shot_examples(self):
        few_shot_examples = ""
        for value in self.state:
            for key, input_string in value.items():
                if "few_shot_examples" in key:
                    few_shot_examples = input_string
                    
        return few_shot_examples
    
    def _parse_db_schema(self):
        db_schema = {}
        for value in self.state:
            for key, input_string in value.items():
                if "sql_db_schema" in key:
                    db_schema = input_string
        return db_schema

    def _parse_data_model_context(self):
        data_model_context = ""
        for value in self.state:
            for key, input_string in value.items():
                if "data_model_context" in key:
                    data_model_context = input_string
        return data_model_context
    def _create_sql_query(self,user_input):
        
        few_shot_examples = self._parse_few_shot_examples()
        db_schema = self._parse_db_schema()
        data_model_context = self._parse_data_model_context()
        prompt_input = PromptTemplate(
            input_variables=["db_schema", "user_input", "few_shot_examples","data_model_context"],
            template=self.SQL_QUERY_CREATOR_TEMPLATE,
        )
        query_creator_chain = LLMChain(llm=self.sqlcreatorllm, prompt=prompt_input)

        sql_query = query_creator_chain.run(
                    (
                        {
                            "db_schema": db_schema,
                            "user_input": user_input,
                            "few_shot_examples": few_shot_examples,
                             "data_model_context": data_model_context
                        }
                    )
                )
        sql_query = sql_query.replace("```","")
        sql_query = sql_query.replace("sql","")
        
        return sql_query
    
    def _extract_sql_query(self):
        for value in self.state:
            for key, input_string in value.items():
                if "sql_db_query_creator" in key:
                    return input_string
        return None