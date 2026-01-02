import icon
from shiny import App, ui, reactive, render, run_app
from data_collection import *  # assumes sc, league_names_df, cat_leagues, team_names_df, etc. are defined
import yahoo_fantasy_api as yfa
import pandas as pd

app_ui = ui.page_fluid(
    ui.output_ui("login_area"),
    ui.output_ui("main_screen"),
)


def server(input, output, session):
    # ---------- state ----------
    has_entered = reactive.Value(False)
    selected_team = reactive.Value(None)
    selected_league = reactive.Value(None)
    trade_blocks = reactive.Value([])

    # ---------- reactive derived values ----------

    @reactive.Calc
    def league_id():
        name = input.user_league_name()
        if not name:
            return None
        ids = league_names_df.loc[
            league_names_df["name"] == name, "League Ids"
        ].tolist()
        return ids[0] if ids else None

    @reactive.Calc
    def active_league():
        lid = league_id()
        if lid is None:
            return None
        game = yfa.Game(sc, "nhl")
        return game.to_league(lid)

    @reactive.Calc
    def active_teams():
        lg = active_league()
        if lg is None:
            return []
        standings = lg.standings()
        df = pd.json_normalize(standings)
        return df["name"].tolist()

    @reactive.Calc
    def your_team_roster():
        team = selected_team.get()
        if not team:
            return []
        rows = team_names_df.loc[team_names_df["team_name"] == team, "Team Roster"]
        if rows.empty:
            return []
        roster_value = rows.iloc[0]
        return roster_value if isinstance(roster_value, list) else []

    @reactive.Calc
    def trade_partner_roster():
        partner = input.trade_partner()
        if not partner:
            return []
        rows = team_names_df.loc[team_names_df["team_name"] == partner, "Team Roster"]
        if rows.empty:
            return []
        roster_value = rows.iloc[0]
        return roster_value if isinstance(roster_value, list) else []

    @reactive.Calc
    def active_categories():
        league_name = selected_league.get() or input.user_league_name()
        if not league_name:
            return []
        rows = cat_leagues.loc[cat_leagues["name"] == league_name, "Categories"]
        if rows.empty:
            return []
        cats_value = rows.iloc[0]
        return cats_value if isinstance(cats_value, list) else []

    # JS condition string: show category selector if user_league_name is one of the cat_leagues
    cat_league_names = cat_leagues["name"].tolist()
    cats_condition = (
        "input.user_league_name !== null && "
        f"{cat_league_names!r}.includes(input.user_league_name)"
    )

    # ---------- login area ----------

    @output()
    @render.ui
    def login_area():
        if not has_entered.get():
            return ui.card(
                ui.h4("Login area"),
                ui.input_selectize(
                    "user_league_name",
                    "Select Your League",
                    choices=league_names_df["name"].tolist(),
                ),
                ui.input_selectize(
                    "user_team_name",
                    "Select your team",
                    choices=[],
                ),
                ui.input_action_button("submit_team", "Continue"),
            )
        return None

    @reactive.Effect
    @reactive.event(input.user_league_name)
    def _update_teams():
        ui.update_selectize("user_team_name", choices=active_teams())

    @reactive.Effect
    @reactive.event(input.submit_team)
    def _unlock_app():
        team = input.user_team_name()
        if team and team in active_teams():
            selected_team.set(team)
            selected_league.set(input.user_league_name())
            has_entered.set(True)

    # ---------- main screen UI ----------

    @output()
    @render.ui
    def main_screen():
        if not has_entered.get():
            return None

        return ui.page_navbar(
            # ----- Team Comparison -----
            ui.nav_panel(
                "AI Assistance",
                ui.input_text(
                    "chat_input",
                    "Ask A Question",
                    value= "",
                    update_on= "change"
                ),
                ui.input_action_button(
                    "submit_request",
                    "Generate Response",
                    icon= "play"
                )
            ),

            # ----- Trade Block Adder -----
            ui.nav_panel(
                "Trade Block Adder",
                ui.panel_conditional(
                    cats_condition,
                    ui.input_selectize(
                        "category_selector",
                        "Select Categories",
                        choices=[],
                        multiple=True,
                    ),
                ),
                ui.input_selectize(
                    "player_adder",
                    "Add Players to Your Trade Block",
                    choices=[],
                    multiple=True,
                ),
                ui.input_action_button("submit_trade_block", "Save Trade Block"),
            ),

            # ----- Trade Block Viewer -----
            ui.nav_panel(
                "Trade Block Viewer",
                ui.input_selectize(
                    "view_block",
                    "Select a Team",
                    choices=team_names_df["team_name"].tolist(),
                    multiple=False,
                ),
            ),

            # ----- Trade Simulator -----
            ui.nav_panel(
                "Trade Simulator",
                ui.input_selectize(
                    "add_your_players",
                    "Add Players You Want to Trade",
                    choices=[],
                    multiple=True,
                ),
                ui.input_selectize(
                    "trade_partner",
                    "Select Team to Trade With",
                    choices=[t for t in active_teams() if t != selected_team.get()],
                ),
                ui.input_selectize(
                    "add_other_players",
                    "Add Players You Want to Trade For",
                    choices=[],
                    multiple=True,
                ),
                ui.input_action_button("submit_trade", "Submit Trade"),
            ),

            title="Fantasy Trade Analyzer",
            id="trade_block_navbar",
            navbar_options=ui.navbar_options(position="fixed-bottom"),
        )



    # ---------- dynamic updates after login ----------

    @reactive.Effect
    @reactive.event(input.submit_request)
    def ai_logic():
        user_roster = your_team_roster()
        return None

    @reactive.Effect
    @reactive.event(has_entered, selected_team)
    def _init_main_screen_inputs():
        """Initialize main screen inputs when app unlocks"""
        if has_entered.get() and selected_team.get():
            roster = your_team_roster()
            cats = active_categories()

            ui.update_selectize("player_adder", choices=roster)
            ui.update_selectize("add_your_players", choices=roster)
            ui.update_selectize("category_selector", choices=cats)

    @reactive.Effect
    @reactive.event(input.trade_partner)
    def _update_trade_partner_roster():
        partner_roster = trade_partner_roster()
        ui.update_selectize("add_other_players", choices=partner_roster)

    # ---------- trade block submit ----------

    @reactive.Effect
    @reactive.event(input.submit_trade_block)
    def _submit_trade_block():
        curr_team = selected_team.get()
        curr_league_name = selected_league.get()
        team_trade_block = input.player_adder() or []

        blocks = trade_blocks.get().copy()
        blocks.append({
            "team": curr_team,
            "league": curr_league_name,
            "trade_block": team_trade_block,
        })

        if curr_league_name in cat_leagues["name"].values:
            team_cats_needed = input.category_selector() or []
            blocks.append({
                "team": curr_team,
                "league": curr_league_name,
                "categories_needed": team_cats_needed,
            })

        trade_blocks.set(blocks)

    # ---------- trade block viewer (placeholder) ----------

    @reactive.Effect
    @reactive.event(input.view_block)
    def _view_trade_block():
        team_to_view = input.view_block()
        # Add display logic here
        pass

    # ---------- trade submit (placeholder) ----------

    @reactive.Effect
    @reactive.event(input.submit_trade)
    def _submit_trade():
        # Implement trade simulation logic here
        pass


app = App(app_ui, server)

if __name__ == "__main__":
    run_app(app)
