# flake8: noqa

# Team-specific lookups and model features. The inherited event_counts() method
# aggregates across the team, while model_data() keeps each member separate.

from .query_base import QueryBase

from .sql_execution import QueryMixin


class Team(QueryBase):

    # Shared queries use this value to select the team table and team_id.
    name = "team"

    def names(self):

        # Return (team name, team ID) tuples for the same dropdown interface
        # used by Employee.names().
        query_5 = f"""
        SELECT team_name, team_id
        FROM team
        """
        return self.query(query_5)

    def username(self, id):

        # Return [(team_name,)] for a matching ID, or [] when the ID is absent.
        # As in the shared queries, the interpolated ID must be a trusted number.
        query_6 = f"""
        SELECT team_name FROM team WHERE team_id = {id}
        """
        return self.query(query_6)

    def model_data(self, id):

        # Filter to the team, then sum each member's event history independently.
        # The outer SELECT drops employee_id, leaving only the two model features
        # in training order. BarChart predicts per member and averages the scores.
        query__ = f"""
            SELECT positive_events, negative_events FROM (
                    SELECT employee_id
                         , SUM(positive_events) positive_events
                         , SUM(negative_events) negative_events
                    FROM {self.name}
                    JOIN employee_events
                        USING({self.name}_id)
                    WHERE {self.name}.{self.name}_id = {id}
                    GROUP BY employee_id
                   )
                """
        return self.pandas_query(query__)
