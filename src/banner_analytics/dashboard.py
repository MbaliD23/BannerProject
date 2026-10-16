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

PURPLE = "#6842D9"
PURPLE_DARK = "#43248F"
PURPLE_MID = "#A98CEA"
PURPLE_LIGHT = "#EEE8FF"
YELLOW = "#C9A227"
YELLOW_DARK = "#8C6B10"
YELLOW_LIGHT = "#FFF4C2"
TEAL = "#2B827B"
INK = "#1D1B24"
PLOT_COLOURS = [PURPLE, YELLOW, TEAL, PURPLE_DARK, PURPLE_MID, "#E3C85A"]
SITE_COLOURS = {"Hollywoodbets": PURPLE, "LuckyFish": YELLOW}


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
    with st.container(gap="small"):
        st.badge("Marketing intelligence", icon=":material/query_stats:", color="violet")
        st.title("Banner Analytics", icon=":material/analytics:")
        st.caption(
            "A clear daily view of promotional activity across LuckyFish and Hollywoodbets — from live creative to long-term competitor signals."
        )


def _premium_polish() -> None:
    """Small, stable visual refinements layered on top of the native theme."""
    st.html(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 78% 0%, rgba(104, 66, 217, 0.055), transparent 30rem),
                radial-gradient(circle at 20% 12%, rgba(201, 162, 39, 0.045), transparent 26rem),
                #F5F5F7;
        }
        [data-testid="stHeader"] {
            background: rgba(245, 245, 247, 0.78);
            backdrop-filter: blur(18px) saturate(150%);
            -webkit-backdrop-filter: blur(18px) saturate(150%);
        }
        [data-testid="stSidebar"] {
            box-shadow: 12px 0 40px rgba(17, 13, 25, 0.10);
        }
        [data-testid="stMetric"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            box-shadow: 0 10px 30px rgba(29, 27, 36, 0.055);
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.88);
        }
        [data-testid="stImage"] img {
            border-radius: 0.85rem;
        }
        .stPlotlyChart {
            border-radius: 1rem;
            overflow: hidden;
        }
        </style>
        """
    )


def _sidebar(frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    with st.sidebar:
        st.markdown("## Banner Analytics")
        st.caption("DAILY CAMPAIGN INTELLIGENCE")
        st.space("small")
        st.markdown("#### Workspace")
        page = st.radio(
            "Navigation",
            ["Overview", "Banner gallery", "Trend analytics", "Competitor comparison", "Insights & exports", "Operations"],
            label_visibility="collapsed",
        )
        st.markdown("#### Refine this view")
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
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color=INK, size=13),
        title=dict(font=dict(size=17, color=INK), x=0.01, xanchor="left"),
        margin=dict(l=20, r=28, t=76, b=30),
        legend_title_text="",
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=INK, bordercolor="#D8D3E2", font_size=13),
        modebar=dict(bgcolor="rgba(255,255,255,.72)"),
    )
    fig.update_xaxes(gridcolor="rgba(29,27,36,.07)", linecolor="rgba(29,27,36,.12)", automargin=True)
    fig.update_yaxes(gridcolor="rgba(29,27,36,.07)", linecolor="rgba(29,27,36,.12)", automargin=True)
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
    st.space("small")
    st.subheader("Current promotional landscape", icon=":material/monitoring:")
    st.caption("How campaign volume and creative themes are moving across both competitors.")
    counts = frame.groupby([pd.Grouper(key="capture_date", freq="MS"), "website"]).size().reset_index(name="banners") if total else pd.DataFrame()
    if not counts.empty:
        frequency = px.line(
            counts,
            x="capture_date",
            y="banners",
            color="website",
            markers=True,
            title="Promotion frequency over time",
            color_discrete_map=SITE_COLOURS,
            labels={"capture_date": "Month", "banners": "Banner captures", "website": "Website"},
        )
        frequency.update_traces(
            line=dict(width=3),
            marker=dict(size=9, line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %Y}<br>%{y} banner captures<extra></extra>",
        )
        frequency.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        frequency.update_xaxes(tickformat="%b %Y")
        if counts["capture_date"].nunique() == 1:
            centre = counts["capture_date"].iloc[0]
            frequency.update_xaxes(range=[centre - pd.Timedelta(days=16), centre + pd.Timedelta(days=16)])
            frequency.update_yaxes(range=[0, counts["banners"].max() + 1])
        with st.container(border=True):
            _plot(frequency, "overview-frequency", "Interactive monthly promotion frequency by website")

    categories = frame.explode("category_list")["category_list"].value_counts().head(8).rename_axis("category").reset_index(name="count") if total else pd.DataFrame()
    if not categories.empty:
        categories = categories.sort_values("count", ascending=True)
        category_chart = px.bar(
            categories,
            x="count",
            y="category",
            orientation="h",
            title="Leading categories",
            color="category",
            color_discrete_sequence=PLOT_COLOURS,
            labels={"count": "Banner captures", "category": "Promotion category"},
            text="count",
        )
        category_chart.update_traces(
            hovertemplate="<b>%{y}</b><br>%{x} banner captures<extra></extra>",
            textposition="outside",
            cliponaxis=False,
        )
        category_chart.update_layout(showlegend=False, height=max(360, 62 * len(categories)))
        with st.container(border=True):
            _plot(category_chart, "overview-categories", "Banner captures by leading promotion category")
    st.subheader("Recent banner changes", icon=":material/update:")
    recent = frame[frame["is_new"]].sort_values("capture_date", ascending=False).head(8)
    if recent.empty:
        st.info("No new banner changes detected in the selected period.")
    else:
        st.dataframe(recent[["capture_date", "website", "headline", "categories", "max_prize"]], width="stretch", hide_index=True, alt="Recently detected promotional banners")


def gallery(frame: pd.DataFrame) -> None:
    st.subheader("Banner gallery", icon=":material/photo_library:")
    st.caption("Browse the creative, message and offer behind every captured promotion.")
    if frame.empty:
        st.info("No banners match the current filters.")
        return

    with st.container(border=True):
        st.markdown("#### Gallery filters")
        first_row = st.columns(2)
        sort = first_row[0].selectbox(
            "Sort by",
            ["Newest first", "Oldest first", "Highest prize value", "Active promotions first", "Website A–Z"],
        )
        status = first_row[1].segmented_control(
            "Promotion status",
            ["All", "Active", "Newly detected"],
            default="All",
            key="gallery-status",
        )

        captured = pd.to_datetime(frame["capture_date"], utc=True)
        second_row = st.columns(2)
        gallery_dates = second_row[0].date_input(
            "Captured between",
            value=(captured.min().date(), captured.max().date()),
            key="gallery-dates",
        )
        gallery_sites = second_row[1].multiselect(
            "Website",
            sorted(frame["website"].dropna().unique()),
            default=sorted(frame["website"].dropna().unique()),
            key="gallery-sites",
        )
        gallery_categories = st.multiselect(
            "Promotion category",
            sorted({item for values in frame["category_list"] for item in values}),
            key="gallery-categories",
            placeholder="All promotion categories",
        )

    display = frame.copy()
    if gallery_sites:
        display = display[display["website"].isin(gallery_sites)]
    else:
        display = display.iloc[0:0]
    if isinstance(gallery_dates, (tuple, list)) and len(gallery_dates) == 2:
        display_dates = pd.to_datetime(display["capture_date"], utc=True).dt.date
        display = display[(display_dates >= gallery_dates[0]) & (display_dates <= gallery_dates[1])]
    if gallery_categories:
        selected = set(gallery_categories)
        display = display[display["category_list"].apply(lambda values: bool(selected.intersection(values)))]
    if status == "Active":
        display = display[display["is_active"]]
    elif status == "Newly detected":
        display = display[display["is_new"]]

    if sort == "Oldest first":
        display = display.sort_values("capture_date")
    elif sort == "Highest prize value":
        display = display.sort_values("max_prize", ascending=False)
    elif sort == "Active promotions first":
        display = display.sort_values(["is_active", "capture_date"], ascending=[False, False])
    elif sort == "Website A–Z":
        display = display.sort_values(["website", "capture_date"], ascending=[True, False])
    else:
        display = display.sort_values("capture_date", ascending=False)
    st.caption(f"Showing {len(display):,} matching banner captures")
    if display.empty:
        st.info("No banners match the gallery filters. Try widening the date range or clearing a selection.")
        return
    for start in range(0, min(len(display), 60), 2):
        columns = st.columns(2)
        for column, (_, row) in zip(columns, display.iloc[start : start + 2].iterrows()):
            image_value = str(row["image_path"]).strip() if row["image_path"] else ""
            path = Path(image_value) if image_value and not image_value.startswith(("http://", "https://")) else None
            with column.container(border=True, height="stretch"):
                if image_value.startswith(("http://", "https://")):
                    st.image(image_value, width="stretch", alt=f"Promotional banner: {row['headline']}")
                elif path and path.is_file():
                    st.image(str(path), width="stretch", alt=f"Captured banner: {row['headline']}")
                else:
                    st.caption(":material/image: Artwork unavailable for this reference banner")
                captured = pd.to_datetime(row["capture_date"]).strftime("%d %b %Y · %H:%M")
                badge_colour = "yellow" if row["website"] == "LuckyFish" else "violet"
                st.markdown(" ".join(f":{badge_colour}-badge[{item}]" for item in row["category_list"][:2]))
                st.caption(f"{row['website']} · {captured}")
                st.markdown(f"#### {row['headline']}")
                st.caption(str(row["description"]))
                with st.expander("Capture detail", icon=":material/visibility:"):
                    st.write(row["ocr_text"] or "No OCR text detected")
                    st.caption(f"Position {row['position']} · Prize value R{row['max_prize']:,.0f}")


def trends(frame: pd.DataFrame) -> None:
    st.subheader("Trend analytics", icon=":material/trending_up:")
    st.caption("See which campaign themes, keywords and providers are gaining momentum.")
    if frame.empty:
        st.info("No trend data for the current filters.")
        return
    exploded = frame.explode("category_list")
    monthly = exploded.groupby([pd.Grouper(key="capture_date", freq="MS"), "category_list"]).size().reset_index(name="count")
    _plot(px.line(monthly, x="capture_date", y="count", color="category_list", markers=True, title="Promotion category trends", color_discrete_sequence=PLOT_COLOURS), "trend-lines", "Monthly trend for each promotion category")
    left, right = st.columns(2)
    with left:
        site_month = frame.groupby([pd.Grouper(key="capture_date", freq="MS"), "website"]).size().reset_index(name="count")
        _plot(px.bar(site_month, x="capture_date", y="count", color="website", barmode="group", title="Monthly promotion counts", color_discrete_map=SITE_COLOURS), "trend-monthly", "Monthly banner capture count by website")
    with right:
        keywords = Counter(word.strip() for value in frame["keywords"] for word in str(value).split(",") if word.strip())
        keyword_frame = pd.DataFrame(keywords.most_common(10), columns=["keyword", "count"])
        if not keyword_frame.empty:
            _plot(px.bar(keyword_frame, x="count", y="keyword", orientation="h", title="Most recurring keywords", color="count", color_continuous_scale=[YELLOW_LIGHT, PURPLE]), "trend-keywords", "Frequency of recurring promotional keywords")
    brands = Counter(word.strip() for value in frame["brands"] for word in str(value).split(",") if word.strip())
    if brands:
        st.markdown("#### Most advertised games and providers")
        st.dataframe(pd.DataFrame(brands.most_common(), columns=["Brand / provider", "Banner mentions"]), width="stretch", hide_index=True, alt="Most advertised game brands and providers")


def comparison(frame: pd.DataFrame) -> None:
    st.subheader("Competitor comparison", icon=":material/compare_arrows:")
    st.caption("Compare promotional intensity and positioning without losing the underlying evidence.")
    if frame.empty:
        st.info("No comparison data for the current filters.")
        return
    exploded = frame.explode("category_list")
    distribution = exploded.groupby(["website", "category_list"]).size().reset_index(name="count")
    _plot(px.bar(distribution, x="category_list", y="count", color="website", barmode="group", title="Promotion category distribution", color_discrete_map=SITE_COLOURS), "comparison-category", "Category distribution for each competitor")
    left, right = st.columns(2)
    with left:
        prizes = frame[frame["max_prize"] > 0]
        if not prizes.empty:
            _plot(px.box(prizes, x="website", y="max_prize", color="website", points="all", title="Advertised prize value distribution", color_discrete_map=SITE_COLOURS, labels={"max_prize": "Prize value (R)"}), "comparison-prize", "Advertised prize value ranges by competitor")
    with right:
        indicators = ["App Download Promotion", "Welcome Bonus", "Deposit Bonus", "Jackpot Promotion"]
        activity = distribution[distribution["category_list"].isin(indicators)]
        _plot(px.bar(activity, x="category_list", y="count", color="website", barmode="group", title="Strategic activity signals", color_discrete_map=SITE_COLOURS), "comparison-signals", "App, bonus, and jackpot promotion activity by competitor")
    summary = frame.groupby("website").agg(campaigns=("id", "count"), new_campaigns=("is_new", "sum"), active=("is_active", "sum"), highest_prize=("max_prize", "max")).reset_index()
    st.dataframe(summary, width="stretch", hide_index=True, alt="Competitor promotion activity summary")


def insights_exports(frame: pd.DataFrame) -> None:
    st.subheader("Analytical insights", icon=":material/auto_awesome:")
    st.caption("Evidence-led signals calculated directly from the selected campaign data.")
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
    st.subheader("Collection operations", icon=":material/settings_suggest:")
    st.caption("Monitor collection health, schedule settings and configured sources.")
    settings = get_settings()
    with st.container(horizontal=True):
        st.metric("Daily run time", settings.schedule_time, border=True)
        st.metric("Timezone", settings.timezone, border=True)
        st.metric("Configured sites", len(load_sites()), border=True)
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
    _premium_polish()
    settings = get_settings()
    frame, runs, warning = _load_data(settings.demo_mode)
    filtered, page = _sidebar(frame)
    _header()
    if warning or settings.demo_mode:
        label = "Reference snapshot · live database not connected" if settings.demo_mode else "Reference fallback · database offline"
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

