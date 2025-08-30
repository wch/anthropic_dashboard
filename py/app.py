from shiny import App, Inputs, Outputs, Session, ui, render, reactive
from shinyreact import page_bare, render_object
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import random

# Generate sample data (existing)
sample_data = pd.DataFrame(
    {
        "id": range(1, 9),
        "age": [25, 30, 35, 28, 32, 27, 29, 33],
        "score": [85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6],
        "category": ["A", "B", "A", "C", "B", "A", "C", "B"],
    }
)

# Generate dashboard data
monthly_data = pd.DataFrame({
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "desktop": [186, 305, 237, 173, 209, 214, 186, 305, 237, 173, 209, 214],
    "mobile": [80, 200, 120, 190, 130, 140, 80, 200, 120, 190, 130, 140],
    "revenue": [4500, 7200, 5800, 6100, 5400, 6800, 4900, 7500, 6200, 5700, 6300, 7100]
})

# Generate trend data
base_date = datetime(2024, 1, 1)
trend_data = pd.DataFrame({
    "date": [(base_date + timedelta(days=30*i)).strftime("%Y-%m-%d") for i in range(12)],
    "users": np.cumsum([1200, 150, 200, 180, 220, 190, 210, 240, 180, 200, 190, 220]),
    "revenue": np.cumsum([45000, 5200, 6800, 5400, 7200, 6100, 6900, 8100, 5800, 6700, 6400, 7800])
})

app_ui = page_bare(
    ui.head_content(
        ui.tags.script(src="main.js", type="module"),
        ui.tags.link(href="main.css", rel="stylesheet"),
    ),
    ui.div(id="root"),
    title="Shiny + shadcn/ui Example",
)


def server(input: Inputs, output: Outputs, session: Session):
    # === EXISTING OUTPUTS (keep all functionality) ===
    
    @render.text
    def processed_text():
        text = input.user_text() if input.user_text() is not None else ""
        if text == "":
            return ""
        # Simple text processing - uppercase and reverse
        return "".join(reversed(text.upper()))

    @render.text
    def text_length():
        text = input.user_text() if input.user_text() is not None else ""
        return len(text)

    @render.text
    @reactive.event(input.button_trigger)
    def button_response():
        # React to button trigger
        now = datetime.now()
        return f"Event received at: {now.strftime('%Y-%m-%d %H:%M:%S')}.{now.microsecond//10000:02d}"

    # Table data output
    @render_object()
    def table_data():
        return sample_data.to_dict(orient="list")

    # Plot output
    @render.plot()
    def plot1():
        fig, ax = plt.subplots()

        ax.scatter(sample_data["age"], sample_data["score"], s=30, alpha=0.7)

        # Add trend line
        z = np.polyfit(sample_data["age"], sample_data["score"], 1)
        p = np.poly1d(z)
        # Create sorted x values for smooth trend line
        x_trend = np.linspace(sample_data["age"].min(), sample_data["age"].max(), 100)
        ax.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.8)

        ax.set_xlabel("Age")
        ax.set_ylabel("Score")
        ax.set_title("Age vs Score")
        ax.grid(True, alpha=0.3)

        return fig
    
    # === NEW DASHBOARD OUTPUTS ===
    
    # KPI Stats
    @render.text
    def total_users():
        return str(int(trend_data["users"].sum()))
    
    @render.text
    def total_revenue():
        return str(int(monthly_data["revenue"].sum()))
    
    @render.text
    def active_sessions():
        return str(random.randint(800, 1200))  # Simulated real-time data
    
    @render.text
    def conversion_rate():
        return str(round(random.uniform(2.5, 4.8), 1))  # Simulated conversion rate
    
    # Chart data for dashboard
    @render_object()
    def monthly_chart_data():
        return monthly_data.to_dict(orient="list")
    
    @render_object()
    def trend_chart_data():
        return trend_data.to_dict(orient="list")
    
    @render_object()
    def category_chart_data():
        # Aggregate sample data by category
        category_summary = sample_data.groupby("category")["score"].agg(["mean", "count"]).reset_index()
        category_summary.columns = ["category", "score", "count"]
        return category_summary.to_dict(orient="list")
    
    # Activity feed data
    @render_object()
    def activity_feed():
        activities = [
            "New user registered",
            "Payment processed",
            "Report generated",
            "Data exported",
            "User logged in",
            "Settings updated"
        ]
        
        activity_data = pd.DataFrame({
            "id": range(1, 6),
            "activity": random.choices(activities, k=5),
            "timestamp": [(datetime.now() - timedelta(seconds=random.randint(0, 3600))).strftime("%H:%M:%S") for _ in range(5)],
            "user": [f"User {random.randint(100, 999)}" for _ in range(5)]
        })
        
        return activity_data.to_dict(orient="list")


app = App(app_ui, server, static_assets=str(Path(__file__).parent / "www"))
