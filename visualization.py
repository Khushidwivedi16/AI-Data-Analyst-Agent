import pandas as pd
import plotly.express as px

PRIMARY = "#6C63FF"


def _style(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), template="plotly_white", font=dict(size=13))
    return fig


def result_chart(df):
    if df is None or df.empty or df.shape[1] < 2 or not 2 <= len(df) <= 50:
        return None
    x_col = df.columns[0]
    numeric = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric:
        return None
    y_col = numeric[0]
    if pd.api.types.is_datetime64_any_dtype(df[x_col]):
        fig = px.line(df, x=x_col, y=y_col, markers=True, title=f"{y_col} by {x_col}")
        fig.update_traces(line_color=PRIMARY)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", color_discrete_sequence=[PRIMARY])
    return _style(fig)


def distribution_chart(df, column):
    fig = px.histogram(df, x=column, nbins=30, title=f"Distribution of {column}", color_discrete_sequence=[PRIMARY])
    return _style(fig)


def top_categories_chart(df, category_col, value_col, top_n=10):
    grouped = (
        df.groupby(category_col)[value_col]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    fig = px.bar(
        grouped, x=category_col, y=value_col,
        title=f"Top {top_n} {category_col} by total {value_col}",
        color_discrete_sequence=[PRIMARY],
    )
    return _style(fig)