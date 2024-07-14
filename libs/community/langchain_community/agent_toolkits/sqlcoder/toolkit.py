"""Toolkit for interacting with a SQL database."""
from typing import List

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseToolkit

from langchain_community.utilities.sql_database import SQLDatabase

from langchain_community.tools.sql_database.tool import QuerySQLCheckerTool
from langchain_core.pydantic_v1 import Field

from langchain_community.tools import BaseTool
from langchain_community.tools.sql_coder.tool import (
    QuerySparkSQLDataBaseTool,
    SqlQueryCreatorTool,
    RetrySqlQueryCreatorTool
)

class SQLCoderToolkit(BaseToolkit):
    """Toolkit for interacting with SQL databases."""

    db: SQLDatabase = Field(exclude=True)
    llm: BaseLanguageModel = Field(exclude=True)
    db_token: str
    db_host: str
    db_catalog: str
    db_schema: str
    db_warehouse_id: str
    allow_extra_fields = True
    sqlcreatorllm : BaseLanguageModel = Field(exclude=True)
    sql_query_creator_template : str

    @property
    def dialect(self) -> str:
        """Return string representation of dialect to use."""
        return self.db.dialect

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        query_sql_database_tool_description = (
            "Input to this tool is a detailed and correct SQL query, output is a "
            "result from the database. If the query is not correct, an error message "
            "will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. If you encounter an issue with Unknown column "
            "'xxxx' in 'field list', using schema_sql_db to query the correct table "
            "fields."
        )
        return [
            QuerySparkSQLDataBaseTool(
                db=self.db, description=query_sql_database_tool_description
            ),
            QuerySQLCheckerTool(db=self.db, llm=self.llm),
            RetrySqlQueryCreatorTool(sqlcreatorllm=self.sqlcreatorllm),
            SqlQueryCreatorTool(
                sqlcreatorllm=self.sqlcreatorllm , 
                db=self.db,
                db_token=self.db_token,
                db_host=self.db_host,
                db_catalog=self.db_catalog,
                db_schema=self.db_schema,
                db_warehouse_id=self.db_warehouse_id,
                SQL_QUERY_CREATOR_TEMPLATE=self.sql_query_creator_template

            )
        ]
