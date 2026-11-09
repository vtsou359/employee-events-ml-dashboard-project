# flake8: noqa

# Shared event and note queries for Employee and Team. QueryMixin handles the
# SQLite connection and result conversion; subclasses choose the entity scope.

from .sql_execution import QueryMixin


class QueryBase(QueryMixin):

    # Subclasses use employee or team to select both the table and its ID column.
    # The empty base value is a placeholder, not a queryable database table.
    name = ""

    def names(self):
        # The base object offers no dropdown options; concrete entities provide them.
        return []

    def event_counts(self, id):

        # Join through employee_id or team_id, then sum events for each date.
        # Team scope combines every member's events; employee scope selects one person.
        # The result columns are event_date, Positive, and Negative in date order.
        # IDs are interpolated into SQL; callers must supply trusted numeric values.
        table = self.name
        query_1 = f"""
        SELECT event_date
             , SUM(positive_events) AS Positive
             , SUM(negative_events) AS Negative
        FROM {table}
        JOIN employee_events
            USING ({table}_id)
        WHERE {table}_id = {id}
        GROUP BY event_date
        ORDER BY event_date
        """
        return self.pandas_query(query_1)

    def notes(self, id):

        # Notes already contain both entity IDs, so this query needs no join.
        # Return dated text for the selected employee or team, oldest first.
        table = self.name
        query_2 = f"""
        SELECT note_date, note
        FROM notes
        WHERE {table}_id = {id}
        ORDER BY note_date
        """

        return self.pandas_query(query_2)
