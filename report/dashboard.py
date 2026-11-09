# flake8: noqa

# Dashboard flow: select an employee/team, query SQLite, then render charts
# and notes as HTML. Here, model means an Employee/Team data-access object;
# predictor is the fitted classifier used only by the probability chart.

from fasthtml.common import *
import matplotlib.pyplot as plt

from employee_events import QueryBase, Employee, Team

from utils import load_model

from base_components import Dropdown, BaseComponent, Radio, MatplotlibViz, DataTable
from combined_components import FormGroup, CombinedComponent


# Reuse the dropdown renderer for both entity types. Each data-access object
# supplies (display name, database ID) pairs through the same names() method.
class ReportDropdown(Dropdown):

    def build_component(self, entity_id, model):
        # The current entity type supplies the label; the parent builds the options.
        self.label = model.name

        return super().build_component(entity_id, model)

    def component_data(self, entity_id, model):
        return model.names()


# The heading describes the selected entity type, rather than a specific person
# or team. BaseComponent makes this renderer callable within the report.
class Header(BaseComponent):

    def build_component(self, entity_id, model):

        if model.name.lower() == "team":
            return H1("Team Performance and Recruitment Risk")
        elif model.name.lower() == "employee":
            return H1("Employee Performance and Recruitment Risk")
        else:
            return H1(model.name)


# Show accumulated positive and negative event counts over the stored history.
# MatplotlibViz handles converting the plot into an embedded HTML image.
class LineChart(MatplotlibViz):

    def visualization(self, entity_id, model):

        # Both entity types return daily totals with event_date, Positive, and
        # Negative columns; team totals include all members of the selected team.
        df = model.event_counts(entity_id)

        # Treat null values in returned rows as zero. This does not add missing dates.
        df = df.fillna(0)

        # Chronological ordering is required before turning daily totals into
        # running totals; the date index also provides the chart's x-axis.
        df.set_index("event_date", inplace=True)

        df.sort_index(inplace=True)

        # Each plotted value includes all recorded events up to that date.
        df = df.cumsum()

        # The query returns positive counts first, followed by negative counts.
        df.columns = ["Positive", "Negative"]

        fig, ax = plt.subplots()

        # Draw both series on the same axes so their accumulated totals can be compared.
        df.plot(ax=ax)

        self.set_axis_styling(
            ax,
            bordercolor="black",
            fontcolor="black",
        )

        ax.set_title("Cumulative event counts", fontsize=20)
        ax.set_xlabel("Date")
        ax.set_ylabel("Event count")

        return fig


# Convert aggregate event features into a recruitment probability for an employee
# or an average employee probability for a team. Training happens outside this app.
class BarChart(MatplotlibViz):

    # Load the saved classifier when the class is defined and reuse it across renders.
    predictor = load_model()

    def visualization(self, entity_id, model):

        # Employee queries produce one feature row; team queries produce one row
        # per member. Each row contains total positive and negative event counts.
        dt = model.model_data(entity_id)

        # Employee queries use display-oriented aliases; team queries already use
        # these training names. Both queries supply features in the training order.
        dt = dt.rename(
            columns={"Positive": "positive_events", "Negative": "negative_events"}
        )
        predict_prob = self.predictor.predict_proba(dt)

        # The saved binary classifier uses classes [0, 1], so column 1 is P(recruited=1).
        # Slicing gives a one-dimensional array with one probability per feature row.
        positive_probs = predict_prob[:, 1]

        # A team displays the unweighted mean of its members' probabilities,
        # not the probability that at least one member will be recruited.
        if model.name == "team":
            pred = positive_probs.mean()
        else:
            # The employee feature table contains a single row.
            pred = positive_probs[0]

        # These fixed display thresholds map scores to colors; they are not learned
        # by the classifier or validated as decision thresholds in this project.
        if pred < 0.10:
            bar_color = "green"
        elif pred < 0.30:
            bar_color = "orange"
        else:
            bar_color = "red"

        fig, ax = plt.subplots()
        # A fixed 0-to-1 axis keeps the probability scale consistent between views.
        ax.barh([""], [pred], color=bar_color)
        ax.set_xlim(0, 1)
        ax.set_title("Predicted Recruitment Risk", fontsize=20)

        self.set_axis_styling(
            ax,
            bordercolor="black",
            fontcolor="black",
        )


# Both chart instances receive the same entity ID and data-access object;
# the grid wrapper places their rendered images in one layout.
class Visualizations(CombinedComponent):

    children = [LineChart(), BarChart()]

    outer_div_type = Div(cls="grid")


# Supply dated notes for the current entity; DataTable turns the returned
# DataFrame columns and rows into the HTML table. Notes are not model features.
class NotesTable(DataTable):

    def component_data(self, entity_id, model):

        return model.notes(entity_id)


# Changing the radio selection requests a replacement dropdown via HTMX.
# Submitting the form sends the entity type and selected ID to /update_data.
class DashboardFilters(FormGroup):

    id = "top-filters"
    action = "/update_data"
    method = "POST"

    children = [
        Radio(
            values=["Employee", "Team"],
            name="profile_type",
            hx_get="/update_dropdown",
            hx_target="#selector",
        ),
        ReportDropdown(id="selector", name="user-selection"),
    ]


# Render the page sections in this order, passing the same selection to each.
# The component instances are created here and reused by subsequent renders.
class Report(CombinedComponent):

    children = [Header(), DashboardFilters(), Visualizations(), NotesTable()]


# FastHTML supplies the web app and route decorator; one Report instance
# assembles the page for all employee and team routes.
app, rt = fast_app()

report = Report()


# The landing page uses employee 1 as its initial selection.
@rt("/")
def get():
    return report(1, Employee())


# Detail routes convert the URL ID to an integer before querying the database.
# Choosing Employee or Team changes the data scope without changing the page layout.
@rt("/employee/{id}")
def get(id: str):
    return report(int(id), Employee())


@rt("/team/{id}")
def get(id: str):

    return report(int(id), Team())


# Return only the dropdown fragment for the radio control's HTMX request.
# DashboardFilters places the dropdown at index 1; #selector is the swap target.
@app.get("/update_dropdown{r}")
def update_dropdown(r):
    dropdown = DashboardFilters.children[1]
    print("PARAM", r.query_params["profile_type"])
    if r.query_params["profile_type"] == "Team":
        # No entity is selected yet; replace the options with the chosen entity type.
        return dropdown(None, Team())
    elif r.query_params["profile_type"] == "Employee":
        return dropdown(None, Employee())


@app.post("/update_data")
async def update_data(r):
    from fasthtml.common import RedirectResponse

    # These form keys match the name attributes of the radio control and dropdown.
    data = await r.form()
    profile_type = data._dict["profile_type"]
    id = data._dict["user-selection"]
    # Redirect after POST so the browser loads a shareable detail URL with GET.
    # Refreshing that page does not resubmit the selection form.
    if profile_type == "Employee":
        return RedirectResponse(f"/employee/{id}", status_code=303)
    elif profile_type == "Team":
        return RedirectResponse(f"/team/{id}", status_code=303)


# Start the development server using the FastHTML application defined above.
serve()
