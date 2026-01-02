# from shiny import App, ui, reactive, run_app
# from data_collection import *
#
# app_ui = ui.page_navbar(
#     ui.nav_panel(
#         "Log In",
#         ui.input_text("user_team_name", "Please input your team name"),
#         ui.input_action_button("submit", "Submit"),
#     ),
#     ui.nav_panel("Team Comparison",
#                  ui.input_selectize("select_teams", "Select Teams To Compare", team_names_df["team_name"], multiple=True),
#     ),
#     ui.nav_panel("Trade Block Adder",
#                  ui.input_selectize("player_adder", "Add Players to Your Trade Block", full_roster_list, multiple=True),
#     ),
#     ui.nav_panel("Trade Block Viewer",
#                  ui.input_selectize("view_block", "View Teams Trade Block", team_names_df["team_name"], multiple=True),
#     ),
#     ui.nav_panel("Trade Simulator",
#                  ui.input_selectize("add_your_players", "Add Players You Want to Trade", full_roster_list, multiple=True),
#                  ui.input_selectize("add_other_players", "Add Players You Want to Trade For", full_roster_list, multiple=True),
#                  ui.input_action_button("submit_trade", "Submit Trade"),
#     ),
#     title="Trade Block Adder",
#     id="trade_block_navbar",
#     navbar_options=ui.navbar_options(position="fixed-bottom"),
# )
#
# def server(input, output, session):
#     team_name =  input["team_name_checker"]
#     league_name = input["league_name_checker"]
#     player_name = input["player_adder"]
#
# app = App(app_ui, server)
# run_app(app)
# app.run()