from sqlalchemy import text
from sqlalchemy.engine import Connection


def insert_record(
    connection: Connection,
    table_name: str,
    data: dict,
    primary_key: str | None = None,
):

    columns = list(data.keys())

    column_sql = ", ".join(
        f"[{column}]"
        for column in columns
    )

    parameter_sql = ", ".join(
        f":{column}"
        for column in columns
    )

    if primary_key:
        query = text(
            f"""
            INSERT INTO [{table_name}]
            ({column_sql})
            OUTPUT INSERTED.[{primary_key}]
            VALUES
            ({parameter_sql})
            """
        )
    else:
        query = text(
            f"""
            INSERT INTO [{table_name}]
            ({column_sql})
            VALUES
            ({parameter_sql})
            """
        )


    result = connection.execute(
        query,
        data,
    )

    if primary_key:
        return result.scalar_one()

    return result