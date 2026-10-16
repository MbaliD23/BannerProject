from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from .config import get_settings, load_sites
from .demo_data import demo_banners, demo_runs
from .exporter import csv_bytes, excel_bytes
from .repository import filter_frame, load_banner_frame, load_runs_frame

logger = logging.getLogger(__name__)

PURPLE = "#8B5CF6"
TEAL = "#16D9C4"
YELLOW = "#F4D84A"
PINK = "#EF4A82"
PLOT_COLOURS = [PURPLE, TEAL, YELLOW, PINK, "#69A9FF", "#9AE6B4"]


@st.cache_data(ttl=300, show_spinner=False)
def _load_data(demo_mode: bool) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    if demo_mode:
        return demo_banners(), demo_runs(), None
    try:
        return load_banner_frame(), load_runs_frame(), None
    except Exception as exc:
        logger.exception("Unable to load database data")
        return demo_banners(), demo_runs(), str(exc)


def _header() -> None:
    st.badge("Marketing intelligence platform", icon=":material/query_stats:", color="violet")
    st.title("Banner Analytics", icon=":material/analytics:")
    st.caption(
        "Daily promotional monitoring across LuckyFish and Hollywoodbets — with campaign history, competitor signals and export-ready evidence."
    )


def _sidebar(frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    with st.sidebar:
        st.markdown("## Banner Analytics")
        st.caption("PROMOTION INTELLIGENCE")
        page = st.radio(
            "Navigation",
            ["Overview", "Banner gallery", "Trend analytics", "Competitor comparison", "Insights & exports", "Operations"],
            label_visibility="collapsed",
        )
        st.markdown("#### Filters")
        sites = sorted(frame["website"].dropna().unique()) if not frame.empty else []
        selected_sites = st.multiselect("Website", sites, default=sites)
        category_values = sorted({item for values in frame.get("category_list", []) for item in values}) if not frame.empty else []
        selected_categories = st.multiselect("Promotion category", category_values)
        if frame.empty:
            dates = None
        else:
            series = pd.to_datetime(frame["capture_date"], utc=True)
            dates = st.date_input("Capture date", value=(series.min().date(), series.max().date()))
        keyword = st.text_input("Search", placeholder="Headline, keyword or game")
        max_prize = float(frame["max_prize"].max()) if not frame.empty else 0.0
        min_prize = st.number_input("Minimum prize value (R)", min_value=0.0, max_value=max_prize or 1.0, value=0.0, step=1000.0)
        filtered = filter_frame(
            frame,
            websites=selected_sites,
            categories=selected_categories,
            date_range=tuple(dates) if isinstance(dates, (tuple, list)) and len(dates) == 2 else None,
            keyword=keyword,
            min_prize=min_prize,
        )
        st.caption(f"{len(filtered):,} of {len(frame):,} banner captures")
    return filtered, page


def _plot(fig, key: str, alt: str) -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#D6E3E6",
        margin=dict(l=8, r=8, t=48, b=8),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    st.plotly_chart(fig, width="stretch", key=key, alt=alt)


def overview(frame: pd.DataFrame, runs: pd.DataFrame) -> None:
    total = len(frame)
    active = int(frame["is_active"].sum()) if total else 0
    new = int(frame["is_new"].sum()) if total else 0
    success = (runs["status"].eq("success").mean() * 100) if not runs.empty else 0
    cols = st.columns(4)
    cols[0].metric("Captured banners", f"{total:,}", f"{new} newly detected", border=True, height="stretch")
    cols[1].metric("Active promotions", f"{active:,}", border=True, height="stretch")
    cols[2].metric("Websites monitored", frame["website"].nunique() if total else 0, border=True, height="stretch")
    cols[3].metric("Collection success", f"{success:.0f}%", border=True, height="stretch")
    st.subheader("Current promotional landscape")
    left, right = st.columns([1.35, 1])
    with left:
        exploded = frame.explode("category_list") if total else frame
        counts = exploded.groupby([pd.Grouper(key="capture_date", freq="MS"), "website"]).size().reset_index(name="banners") if total else pd.DataFrame()
        if not counts.empty:
            _plot(px.area(counts, x="capture_date", y="banners", color="website", title="Promotion frequency over time", color_discrete_sequence=PLOT_COLOURS), "overview-frequency", "Monthly promotion captures by website")
    with right:
        categories = frame.explode("category_list")["category_list"].value_counts().head(8).rename_axis("category").reset_index(name="count") if total else pd.DataFrame()
        if not categories.empty:
            _plot(px.bar(categories, x="count", y="category", orientation="h", title="Leading categories", color="category", color_discrete_sequence=PLOT_COLOURS), "overview-categories", "Promotion counts by leading category")
    st.subheader("Recent banner changes")
    recent = frame[frame["is_new"]].sort_values("capture_date", ascending=False).head(8)
    if recent.empty:
        st.info("No new banner changes detected in the selected period.")
    else:
        st.dataframe(recent[["capture_date", "website", "headline", "categories", "max_prize"]], width="stretch", hide_index=True, alt="Recently detected promotional banners")


def gallery(frame: pd.DataFrame) -> None:
    st.markdown("### Banner gallery")
    sort = st.selectbox("Sort", ["Newest first", "Oldest first", "Highest prize value"], label_visibility="collapsed")
    if sort == "Oldest first":
        display = frame.sort_values("capture_date")
    elif sort == "Highest prize value":
        display = frame.sort_values("max_prize", ascending=False)
    else:
        display = frame.sort_values("capture_date", ascending=False)
    if display.empty:
        st.info("No banners match the current filters.")
        return
    for start in range(0, min(len(display), 60), 3):
        columns = st.columns(3)
        for column, (_, row) in zip(columns, display.iloc[start : start + 3].iterrows()):
            path = Path(str(row["image_path"])) if row["image_path"] else None
            with column.container(border=True, height="stretch"):
                if path and path.is_file():
                    st.image(str(path), width="stretch", alt=f"Captured banner: {row['headline']}")
                else:
                    st.caption(":material/image: Screenshot not available in demonstration data")
                captured = pd.to_datetime(row["capture_date"]).strftime("%d %b %Y · %H:%M")
                st.markdown(" ".join(f":violet-badge[{item}]" for item in row["category_list"][:2]))
                st.caption(f"{row['website']} · {captured}")
                st.markdown(f"**{row['headline']}**")
                st.caption(str(row["description"]))
                with st.expander("Capture detail", icon=":material/visibility:"):
                    st.write(row["ocr_text"] or "No OCR text detected")
                    st.caption(f"Position {row['position']} · Prize value R{row['max_prize']:,.0f}")


def trends(frame: pd.DataFrame) -> None:
    st.markdown("### Trend analytics")
    if frame.empty:
        st.info("No trend data for the current filters.")
        return
    exploded = frame.explode("category_list")
    monthly = exploded.groupby([pd.Grouper(key="capture_date", freq="MS"), "category_list"]).size().reset_index(name="count")
    _plot(px.line(monthly, x="capture_date", y="count", color="category_list", markers=True, title="Promotion category trends", color_discrete_sequence=PLOT_COLOURS), "trend-lines", "Monthly trend for each promotion category")
    left, right = st.columns(2)
    with left:
        site_month = frame.groupby([pd.Grouper(key="capture_date", freq="MS"), "website"]).size().reset_index(name="count")
        _plot(px.bar(site_month, x="capture_date", y="count", color="website", barmode="group", title="Monthly promotion counts", color_discrete_sequence=PLOT_COLOURS), "trend-monthly", "Monthly banner capture count by website")
    with right:
        keywords = Counter(word.strip() for value in frame["keywords"] for word in str(value).split(",") if word.strip())
        keyword_frame = pd.DataFrame(keywords.most_common(10), columns=["keyword", "count"])
        if not keyword_frame.empty:
            _plot(px.bar(keyword_frame, x="count", y="keyword", orientation="h", title="Most recurring keywords", color="count", color_continuous_scale=["#123640", TEAL]), "trend-keywords", "Frequency of recurring promotional keywords")
    brands = Counter(word.strip() for value in frame["brands"] for word in str(value).split(",") if word.strip())
    if brands:
        st.markdown("#### Most advertised games and providers")
        st.dataframe(pd.DataFrame(brands.most_common(), columns=["Brand / provider", "Banner mentions"]), width="stretch", hide_index=True, alt="Most advertised game brands and providers")


def comparison(frame: pd.DataFrame) -> None:
    st.markdown("### Competitor comparison")
    if frame.empty:
        st.info("No comparison data for the current filters.")
        return
    exploded = frame.explode("category_list")
    distribution = exploded.groupby(["website", "category_list"]).size().reset_index(name="count")
    _plot(px.bar(distribution, x="category_list", y="count", color="website", barmode="group", title="Promotion category distribution", color_discrete_sequence=PLOT_COLOURS), "comparison-category", "Category distribution for each competitor")
    left, right = st.columns(2)
    with left:
        prizes = frame[frame["max_prize"] > 0]
        if not prizes.empty:
            _plot(px.box(prizes, x="website", y="max_prize", color="website", points="all", title="Advertised prize value distribution", color_discrete_sequence=PLOT_COLOURS, labels={"max_prize": "Prize value (R)"}), "comparison-prize", "Advertised prize value ranges by competitor")
    with right:
        indicators = ["App Download Promotion", "Welcome Bonus", "Deposit Bonus", "Jackpot Promotion"]
        activity = distribution[distribution["category_list"].isin(indicators)]
        _plot(px.bar(activity, x="category_list", y="count", color="website", barmode="group", title="Strategic activity signals", color_discrete_sequence=PLOT_COLOURS), "comparison-signals", "App, bonus, and jackpot promotion activity by competitor")
    summary = frame.groupby("website").agg(campaigns=("id", "count"), new_campaigns=("is_new", "sum"), active=("is_active", "sum"), highest_prize=("max_prize", "max")).reset_index()
    st.dataframe(summary, width="stretch", hide_index=True, alt="Competitor promotion activity summary")


def insights_exports(frame: pd.DataFrame) -> None:
    st.markdown("### Analytical insights")
    if frame.empty:
        st.info("No insight data for the current filters.")
        return
    categories = frame.explode("category_list")["category_list"].value_counts()
    highest = frame.loc[frame["max_prize"].idxmax()]
    website = frame["website"].value_counts()
    keywords = Counter(word.strip() for value in frame["keywords"] for word in str(value).split(",") if word.strip())
    insights = [
        f"{categories.index[0]} is the most frequent promotion category, appearing in {categories.iloc[0]} captures.",
        f"The highest advertised prize is R{highest['max_prize']:,.0f}, promoted by {highest['website']}.",
        f"{website.index[0]} has the highest promotional activity in the selected period ({website.iloc[0]} captures).",
        f"The strongest recurring keyword is “{keywords.most_common(1)[0][0]}”." if keywords else "No recurring promotional keyword is dominant yet.",
    ]
    for insight in insights:
        with st.container(border=True):
            st.markdown(f":material/lightbulb: {insight}")
    st.markdown("### Reporting exports")
    st.caption("Exports reflect the filters currently applied in the sidebar.")
    left, right = st.columns(2)
    left.download_button("Download CSV", csv_bytes(frame), "banner-analytics.csv", "text/csv", width="stretch", icon=":material/download:")
    right.download_button("Download Excel", excel_bytes(frame), "banner-analytics.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch", icon=":material/download:")
    st.dataframe(frame[[column for column in ["capture_date", "website", "headline", "categories", "max_prize", "keywords"] if column in frame]], width="stretch", hide_index=True, alt="Banner records included in the current report export")


def operations(runs: pd.DataFrame, data_warning: str | None) -> None:
    st.markdown("### Collection operations")
    settings = get_settings()
    col1, col2, col3 = st.columns(3)
    col1.metric("Daily run time", settings.schedule_time)
    col2.metric("Timezone", settings.timezone)
    col3.metric("Configured sites", len(load_sites()))
    if data_warning:
        st.warning("Database unavailable; showing the built-in demonstration dataset. Start PostgreSQL and initialize the schema to use live data.")
        with st.expander("Technical detail"):
            st.code(data_warning)
    st.markdown("#### Recent collection runs")
    if runs.empty:
        st.info("No collection runs recorded.")
    else:
        st.dataframe(runs, width="stretch", hide_index=True, alt="Recent collection run outcomes")
    st.markdown("#### Site configuration")
    st.dataframe(pd.DataFrame([{"Site": site["name"], "URL": site["url"], "Enabled": site["enabled"]} for site in load_sites()]), width="stretch", hide_index=True, alt="Configured banner monitoring websites")
    st.info("Operational collection is intentionally executed by the scheduler service, not by a Streamlit rerun. This prevents duplicate browser jobs when users interact with the dashboard.")


def main() -> None:
    st.set_page_config(page_title="Banner Analytics", page_icon=":material/analytics:", layout="wide", initial_sidebar_state="expanded")
    settings = get_settings()
    frame, runs, warning = _load_data(settings.demo_mode)
    filtered, page = _sidebar(frame)
    _header()
    if warning or settings.demo_mode:
        label = "Demo data" if settings.demo_mode else "Demo fallback · database offline"
        st.caption(f"● {label}")
    pages = {
        "Overview": lambda: overview(filtered, runs),
        "Banner gallery": lambda: gallery(filtered),
        "Trend analytics": lambda: trends(filtered),
        "Competitor comparison": lambda: comparison(filtered),
        "Insights & exports": lambda: insights_exports(filtered),
        "Operations": lambda: operations(runs, warning),
    }
    pages[page]()

