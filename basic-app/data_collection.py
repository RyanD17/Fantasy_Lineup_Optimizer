# data_collection.py
from yahoo_fantasy_api import *
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
import pandas as pd
import itertools

# Authenticate using credentials from oauth2.json
sc = OAuth2(None, None, from_file='oauth2.json')
sc.refresh_access_token()

# Get game and league IDs
game = yfa.Game(sc, 'nhl')
league_ids = game.league_ids(year=2025)

# ========== SINGLE COMPREHENSIVE DATAFRAME ==========
all_data = []

print("Collecting data for all leagues...")

for lid_idx, league_id in enumerate(league_ids):
    print(f"Processing league {lid_idx + 1}/{len(league_ids)}: {league_id}")

    # League info
    curr_league = game.to_league(league_id)
    league_settings = curr_league.settings()
    league_name = league_settings.get("name", f"League {league_id}")
    scoring_type = league_settings.get("scoring_type", "unknown")

    # Categories (only for head-to-head leagues)
    categories = []
    if scoring_type == "head":
        try:
            cats = curr_league.stat_categories()
            categories = [cat["display_name"] for cat in cats]
        except:
            categories = []

    # Team data for this league
    try:
        standings = curr_league.standings()
        teams = curr_league.teams()

        for team_key, team_data in teams.items():
            # Team basic info
            team_name = team_data.get("name", "Unknown Team")
            team_id = team_data.get("team_id", "")

            # Manager info
            manager = {}
            if team_data.get("managers"):
                manager = team_data["managers"][0]["manager"]

            # Roster
            try:
                team_obj = Team(sc, team_key)
                roster = team_obj.roster()
                roster_players = [player["name"] for player in roster]
            except:
                roster_players = []

            # Add to master dataframe
            all_data.append({
                "league_id": league_id,
                "league_name": league_name,
                "scoring_type": scoring_type,
                "team_name": team_name,
                "team_id": team_id,
                "team_key": team_key,
                "roster_players": roster_players,
                "categories": categories if scoring_type == "head" else [],
                "waiver_priority": team_data.get("waiver_priority", ""),
                "number_of_moves": team_data.get("number_of_moves", ""),
                "number_of_trades": team_data.get("number_of_trades", ""),
                "manager_nickname": manager.get("nickname", ""),
                "manager_email": manager.get("email", ""),
            })

    except Exception as e:
        print(f"Error processing league {league_id}: {e}")
        continue

# ========== CREATE SINGLE MASTER DATAFRAME ==========
master_df = pd.DataFrame(all_data)

print(f"\n✅ Master dataframe created successfully!")
print(f"Shape: {master_df.shape}")
print(f"Columns: {master_df.columns.tolist()}")
print("\nSample data:")
print(master_df.head())

# ========== COMPATIBILITY DATAFRAMES FOR APP ==========
# These match exactly what your Shiny app expects
league_names_df = master_df[["league_name", "league_id", "scoring_type"]].drop_duplicates().reset_index(drop=True)
league_names_df.columns = ["name", "League Ids", "Scoring Type"]

# FIXED: team_names_df (handle unhashable lists in roster_players)
team_names_raw = master_df[["team_name", "roster_players"]].copy()
team_names_raw["roster_tuple"] = team_names_raw["roster_players"].apply(tuple)
team_names_df = team_names_raw.drop_duplicates(subset=["team_name"]).reset_index(drop=True)
team_names_df = team_names_df[["team_name", "roster_players"]]  # Keep original list column
team_names_df.columns = ["team_name", "Team Roster"]

# FIXED: Category leagues (handle unhashable lists)
cat_leagues_raw = master_df[master_df["scoring_type"] == "head"][["league_name", "categories"]].copy()
cat_leagues_raw["categories_tuple"] = cat_leagues_raw["categories"].apply(tuple)
cat_leagues = cat_leagues_raw.drop_duplicates(subset=["league_name"]).reset_index(drop=True)
cat_leagues = cat_leagues[["league_name", "categories"]]  # Keep original list column
cat_leagues.columns = ["name", "Categories"]

# Clean up temporary dataframes
del team_names_raw, cat_leagues_raw

# ========== EXPORTS FOR APP ==========
print("\n📊 Exported dataframes for Shiny app:")
print("- league_names_df:", league_names_df.shape)
print("- team_names_df:", team_names_df.shape)
print("- cat_leagues:", cat_leagues.shape)

# Debug samples
print("\n🔍 Sample league_names_df:")
print(league_names_df.head())
print("\n🔍 Sample team_names_df:")
print(team_names_df.head())
print("\n🔍 Sample cat_leagues:")
print(cat_leagues.head())

print("\n✅ data_collection.py fully loaded! All dataframes ready for Shiny app.")
