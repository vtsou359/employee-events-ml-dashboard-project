# flake8: noqa

# Employee-specific lookups and model features. Daily event totals and dated
# notes are inherited from QueryBase through the same interface used by Team.

from .query_base import QueryBase

from .sql_execution import QueryMixin


class Employee(QueryBase):

    # Shared queries use this value to select the employee table and employee_id.
    name = "employee"

    def names(self):

        # Dropdown options are (full name, employee ID) tuples: the name is shown
        # in the UI, while the ID is submitted as the selected entity.
        query_3 = """
        SELECT first_name || ' ' || last_name full_name, employee_id
        FROM employee
        """
        return self.query(query_3)

    def username(self, id):

        # A matching ID returns [(full_name,)]; no match returns an empty list.
        # As in the shared queries, the interpolated ID must be a trusted number.
        query_4 = f"""
        SELECT first_name || ' ' || last_name full_name
        FROM employee
        WHERE employee_id = {id}
        """
        return self.query(query_4)

    def model_data(self, id):

        # Collapse all stored events for one employee into a single feature row.
        # Positive precedes Negative, matching the classifier's feature order;
        # BarChart renames these aliases to the feature names used during training.
        query_ = f"""
        SELECT SUM(positive_events) AS Positive , SUM(negative_events) AS Negative
        FROM {self.name}
        JOIN employee_events
            USING({self.name}_id)
        WHERE {self.name}.{self.name}_id = {id}
        """
        return self.pandas_query(query_)
