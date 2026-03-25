import gradio as gr
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv3


def fetch_scores(selected_date: str) -> str:
    if not selected_date:
        return "<p style='color:#aaa;'>Please select a date.</p>"

    # gr.DateTime with type='string' returns formats like "2026-03-24" or "2026-03-24 00:00:00"
    # Handle float timestamps (fallback) or string values
    try:
        if isinstance(selected_date, (int, float)):
            from datetime import timezone
            date_obj = datetime.fromtimestamp(selected_date, tz=timezone.utc).date()
        else:
            date_obj = datetime.strptime(str(selected_date)[:10], "%Y-%m-%d").date()
    except ValueError:
        return "<p style='color:#f87171;'>Invalid date format. Please use the date picker.</p>"

    today = datetime.now().date()
    if date_obj >= today:
        return "<p style='color:#f87171;'>Please select a date prior to today.</p>"

    date_str = date_obj.strftime("%Y-%m-%d")

    try:
        board = scoreboardv3.ScoreboardV3(game_date=date_str)
        data = board.get_dict()
        games = data["scoreboard"]["games"]
    except Exception as e:
        return f"<p style='color:#f87171;'>Error fetching data: {e}</p>"

    if not games:
        return f"<p style='color:#aaa;'>No games found for {date_str}.</p>"

    cards_html = ""
    for game in games:
        home = game["homeTeam"]
        away = game["awayTeam"]
        status = game["gameStatusText"]

        home_score = home["score"]
        away_score = away["score"]
        home_wins = home_score > away_score
        away_wins = away_score > home_score

        win_color = "#4ade80"
        neutral = "#e2e8f0"

        home_color = win_color if home_wins else neutral
        away_color = win_color if away_wins else neutral

        home_leader = game["gameLeaders"]["homeLeaders"]
        away_leader = game["gameLeaders"]["awayLeaders"]

        home_leader_str = (
            f"{home_leader['name']} &mdash; "
            f"{home_leader['points']} pts / {home_leader['rebounds']} reb / {home_leader['assists']} ast"
            if home_leader.get("name")
            else "N/A"
        )
        away_leader_str = (
            f"{away_leader['name']} &mdash; "
            f"{away_leader['points']} pts / {away_leader['rebounds']} reb / {away_leader['assists']} ast"
            if away_leader.get("name")
            else "N/A"
        )

        cards_html += f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 22px 26px;
            min-width: 300px;
            max-width: 380px;
            font-family: 'Segoe UI', Arial, sans-serif;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        ">
            <div style="text-align:center; color:#94a3b8; font-size:12px; letter-spacing:1px; text-transform:uppercase; margin-bottom:16px;">
                {status}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
                <div style="text-align:center; flex:1;">
                    <div style="font-size:24px; font-weight:700; color:{away_color}; letter-spacing:1px;">{away['teamTricode']}</div>
                    <div style="font-size:12px; color:#64748b; margin-top:2px;">{away['teamCity']} {away['teamName']}</div>
                    <div style="font-size:12px; color:#64748b;">{away['wins']}&ndash;{away['losses']}</div>
                    <div style="font-size:48px; font-weight:800; color:{away_color}; margin-top:8px; line-height:1;">{away_score}</div>
                </div>
                <div style="text-align:center; color:#475569; font-size:14px; font-weight:600; padding-bottom:20px;">@</div>
                <div style="text-align:center; flex:1;">
                    <div style="font-size:24px; font-weight:700; color:{home_color}; letter-spacing:1px;">{home['teamTricode']}</div>
                    <div style="font-size:12px; color:#64748b; margin-top:2px;">{home['teamCity']} {home['teamName']}</div>
                    <div style="font-size:12px; color:#64748b;">{home['wins']}&ndash;{home['losses']}</div>
                    <div style="font-size:48px; font-weight:800; color:{home_color}; margin-top:8px; line-height:1;">{home_score}</div>
                </div>
            </div>
            <hr style="border:none; border-top:1px solid #1e3a5f; margin:16px 0;">
            <div style="font-size:12px; color:#94a3b8; line-height:1.8;">
                <div><span style="color:#cbd5e1; font-weight:600;">{away['teamTricode']}:</span> {away_leader_str}</div>
                <div><span style="color:#cbd5e1; font-weight:600;">{home['teamTricode']}:</span> {home_leader_str}</div>
            </div>
        </div>
        """

    return f"""
    <div style="padding: 8px 0;">
        <h2 style="font-family:'Segoe UI',Arial,sans-serif; color:#e2e8f0; margin-bottom:20px;">
            Scores &mdash; {date_str}
            <span style="font-size:14px; color:#64748b; font-weight:400; margin-left:8px;">({len(games)} game{'s' if len(games) != 1 else ''})</span>
        </h2>
        <div style="display:flex; flex-wrap:wrap; gap:16px;">
            {cards_html}
        </div>
    </div>
    """


yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

with gr.Blocks(
    title="NBA Scores",
    theme=gr.themes.Base(
        primary_hue="blue",
        neutral_hue="slate",
    ),
    css="""
        body { background: #0f172a; }
        .gradio-container { max-width: 1200px !important; }
        #title { text-align: center; }
        #title h1 { color: #f1f5f9; font-size: 2.2rem; margin-bottom: 4px; }
        #title p { color: #64748b; }
    """,
) as demo:
    with gr.Column():
        gr.HTML(
            value="""
            <div id="title">
                <h1>🏀 NBA Scores</h1>
                <p>Select any past date to view game results and top performers.</p>
            </div>
            """
        )

        with gr.Row(equal_height=True):
            date_input = gr.DateTime(
                label="Date",
                value=yesterday,
                include_time=False,
                type="string",
            )
            fetch_btn = gr.Button("Get Scores", variant="primary", scale=0, min_width=140)

        output = gr.HTML()

    fetch_btn.click(fn=fetch_scores, inputs=date_input, outputs=output)
    demo.load(fn=fetch_scores, inputs=date_input, outputs=output)

if __name__ == "__main__":
    demo.launch()

