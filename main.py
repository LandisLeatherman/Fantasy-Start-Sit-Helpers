"""fantasy Football Start/Sit Helper.

The user will enter a players weekly ponits, turnovers, opponent strenght, home/away, and injurt status.
The cite will use this information to score each player and recommend whcih player to start at which position
This is for a PPR League which mean for each per reception a player gets, they score 1 point."""




from bakery import assert_equal
from dataclasses import dataclass
from drafter import *

POSITIONS = ["QB", "RB", "WR", "TE"]
#Average Fantasy points an oppoent allows to each position. 
LEAGUE_AVERAGE_ALLOWED = {"QB": 16.7, "RB": 22.2, "WR": 31.6, "TE": 14.0}
SEASON_WEIGHT = 0.4 #How much the season average counts
RECENT_WEIGHT = 0.6 #How much the last 3-Games average counts
HOME_BONUS = 1.05 #The multiplyer given for players who are at home
TURNOVER_PENALTY= 2.0 #Points lost per turnover per game (fumble lost or an interception)

@dataclass
class Player:
    """The first player the user wants to compare"""
    name: str
    position: str
    points_per_game: list[int]
    fumbles: int               #total fumbles lost this season
    interceptions: int         #total interceptions thrown (for a non-qb this number is 0)
    opponent_allowed: float    #average fantasy points the opponent allows to this position
    home_game: bool
    unavailable: bool #injured or on a bye week

@dataclass
class State:
    """Everything the site remembers between pages"""
    players: list[Player]
    position: str
    recommendation: str
    error_message: str

def parse_scores(text: str) -> list[int]:
    """Turn text such as '10, 12, 8' into [10, 12, 8]
    return [] if any piece is not a whole number"""
    scores = []
    for piece in text.split(","):
        cleaned = piece.strip()
        if not cleaned.lstrip("-").isdigit():
            return []
        scores.append(int(cleaned))
    return scores

def is_number(text: str) -> bool:
    """Check if text is a non-negative number"""
    return text.strip().replace(".", "", 1).isdigit()

def validate_player(name: str, scores: str, fumbles: str, interceptions: str, allowed: str) -> str:
    """return an error message for bad form input, or an empty string if everything is valid"""
    if name.strip() == "":
        return "Please enter a player name."
    if len(parse_scores(scores)) == 0:
        return "Enter points per game as a whole numbers seperates by commas, like 12, 8, 20."
    if not fumbles.strip().isdigit() or not interceptions.strip().isdigit():
        return "Fumbles and intercpetions must be whole numbers (use 0 if none)."
    if not is_number(allowed):
        return "Opponent points allowed must be a number like 24.5"
    return ""

def season_average(scores: list[int]) -> float:
    """Average of all weekly scores (0.0 if there are none, so as to never divide by zero)."""
    if len(scores) == 0:
        return 0.0
    return sum(scores) / len(scores)


def recent_average(scores: list[int]) -> float:
    """Average of the last 3 weekly scores (or fewer if the player has played fewer games)."""
    return season_average(scores[-3:])


def matchup_factor(player: Player) -> float:
    """Above 1.0 means a good matchup (oppoent allows a lot), below 1.0 means a tough one."""
    return player.opponent_allowed / LEAGUE_AVERAGE_ALLOWED.get(player.position, 15.0)

def player_score(player: Player) -> float:
    """Combine form, matchup, home field and turnovers into one comparable score."""
    games = len(player.points_per_game)
    if games == 0:
        return 0.0
    form = (SEASON_WEIGHT * season_average(player.points_per_game) + RECENT_WEIGHT * recent_average(player.points_per_game))
    score = form * matchup_factor(player)
    if player.home_game:
        score = score * HOME_BONUS
    turnovers_per_game = (player.fumbles + player.interceptions) / games
    return score - turnovers_per_game * TURNOVER_PENALTY

def pick_starter(state: State) -> str:
    """Return the name of the best avaiable player at the chosen position ('' if none).
Injured/bye players are skipped (NA). On a tie, the first player entered wins."""
    best_name = ""
    best_score = None

    for player in state.players:
        if player.position == state.position and not player.unavailable:
            score = player_score(player)
            if best_score is None or score > best_score:
                best_score = score
                best_name = player.name
    return best_name

def build_recommendation(state: State) -> str:
    """Write the recommendation text, including which players are NA."""
    starter = pick_starter(state)
    if starter == "":
        message = "No available " + state.position + "s to compare. Add players or mark them healthy."
    else:
        message = "Start " + starter + "!"
    for player in state.players:
        if player.position == state.position and player.unavailable:
            message = message + " NA (injured or on bye): " + player.name + "."
    return message

def describe_player(player: Player) -> str:
    """one line summarizing a player for the players page."""
    status = "NA (injured/bye)" if player.unavailable else "available"
    where = "home" if player.home_game else "away"
    return (f"{player.name} ({player.position}) - season avg {round(season_average(player.points_per_game), 1)}, "
            f"last 3 avg {round(recent_average(player.points_per_game), 1)}, "
            f"fumbles {player.fumbles}, INT {player.interceptions}, "
            f"opponent allows {player.opponent_allowed}, {where}, {status}")
 
 
def starting_players() -> list[Player]:
    """Fictional sample players so the site has something to compare right away."""
    return [
        Player("Sample WR One", "WR", [12, 18, 9, 22, 15], 1, 0, 27.0, True, False),
        Player("Sample WR Two", "WR", [20, 8, 14, 11, 10], 0, 0, 22.0, False, False),
        Player("Sample QB One", "QB", [19, 24, 17, 21, 26], 2, 5, 20.0, False, False),
    ]
 
WR_AVG = LEAGUE_AVERAGE_ALLOWED["WR"] 
assert_equal(parse_scores("10, 12, 8"), [10, 12, 8])
assert_equal(parse_scores("10, x"), [])
assert_equal(parse_scores(""), [])
assert_equal(is_number("24.5"), True)
assert_equal(is_number("abc"), False)
assert_equal(validate_player("", "1,2", "0", "0", "20"), "Please enter a player name.")
assert_equal(validate_player("Ann", "1,2", "0", "0", "20"), "")
assert_equal(validate_player("Ann", "1,b", "0", "0", "20") == "", False)
assert_equal(validate_player("Ann", "1,2", "x", "0", "20") == "", False)
assert_equal(validate_player("Ann", "1,2", "0", "0", "high") == "", False)
assert_equal(season_average([10, 20]), 15.0)
assert_equal(season_average([]), 0.0)
assert_equal(recent_average([1, 100, 10, 10, 10]), 10.0)
assert_equal(recent_average([4, 6]), 5.0)
assert_equal(matchup_factor(Player("A", "WR", [10], 0, 0, WR_AVG / 2, False, False)), 0.5)
assert_equal(player_score(Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False)), 10.0)
assert_equal(player_score(Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, True, False)), 10.5)
assert_equal(player_score(Player("Q", "QB", [10, 10, 10], 3, 3, LEAGUE_AVERAGE_ALLOWED["QB"], False, False)), 6.0)
assert_equal(player_score(Player("E", "WR", [], 0, 0, WR_AVG, False, False)), 0.0)
assert_equal(pick_starter(State([], "WR", "", "")), "")
assert_equal(pick_starter(State([Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False),
                                 Player("B", "WR", [20, 20, 20], 0, 0, WR_AVG, False, False)],
                                "WR", "", "")), "B")
# injured players are skipped
assert_equal(pick_starter(State([Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False),
                                 Player("B", "WR", [20, 20, 20], 0, 0, WR_AVG, False, True)],
                                "WR", "", "")), "A")
# players at other positions are ignored
assert_equal(pick_starter(State([Player("Q", "QB", [30, 30, 30], 0, 0, 18.0, False, False),
                                 Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False)],
                                "WR", "", "")), "A")
# tie: first player entered wins
assert_equal(pick_starter(State([Player("A", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False),
                                 Player("B", "WR", [10, 10, 10], 0, 0, WR_AVG, False, False)],
                                "WR", "", "")), "A")
assert_equal(build_recommendation(State([], "TE", "", "")),
             "No available TEs to compare. Add players or mark them healthy.")
 
 

@route
def index(state: State) -> Page:
    """Home page: explains the site and links to every other page."""
    return Page(state, [
        "Fantasy Football Start/Sit Helper",
        "Not sure who to start this week? Enter your players and the site compares their recent form, "
        "their opponent's defense, home field, and turnovers to recommend the best one.",
        Button("Add a player", add_player_page),
        Button("See my players", players_page),
        Button("Get a recommendation", recommendation_page),
        Button("How it works", how_it_works),
    ])
 
 
@route
def add_player_page(state: State) -> Page:
    """Form for entering one player's information (shows an error message if the last try was invalid)."""
    content = ["Add a player"]
    if state.error_message != "":
        content.append(state.error_message)
    content = content + [
        "Name:", TextBox("name", ""),
        "Position:", SelectBox("position", POSITIONS, "WR"),
        "Fantasy points in each game, oldest first (separate with commas):", TextBox("scores", ""),
        "Fumbles lost this season:", TextBox("fumbles", "0"),
        "Interceptions thrown this season (0 if not a QB):", TextBox("interceptions", "0"),
        "Fantasy points this week's opponent allows per game to this position:", TextBox("allowed", ""),
        "Playing at home this week?", CheckBox("home_game", False),
        "Injured or on a bye week?", CheckBox("unavailable", False),
        Button("Save player", save_player),
        Button("Back", index),
    ]
    return Page(state, content)
 
 
@route
def save_player(state: State, name: str, position: str, scores: str, fumbles: str,
                interceptions: str, allowed: str, home_game: bool, unavailable: bool) -> Page:
    """Validate the form. Save a new Player to state.players, or set state.error_message and show the form again."""
    error = validate_player(name, scores, fumbles, interceptions, allowed)
    if error != "":
        state.error_message = error
        return add_player_page(state)
    new_player = Player(name.strip(), position, parse_scores(scores), int(fumbles), int(interceptions),
                        float(allowed), home_game, unavailable)
    state.players.append(new_player)
    state.error_message = ""
    return players_page(state)
 
 
@route
def players_page(state: State) -> Page:
    """List every player the user has entered."""
    content = ["Your players"]
    for player in state.players:
        content.append(describe_player(player))
    if len(state.players) == 0:
        content.append("No players yet. Add one to get started.")
    content.append(Button("Add another player", add_player_page))
    content.append(Button("Get a recommendation", recommendation_page))
    content.append(Button("Start over", restart))
    content.append(Button("Home", index))
    return Page(state, content)
 
 
@route
def recommendation_page(state: State) -> Page:
    """Pick a position and show who to start."""
    content = [
        "Recommendation",
        "Choose a position to compare:",
        SelectBox("position", POSITIONS, state.position),
        Button("Get recommendation", run_recommendation),
    ]
    if state.recommendation != "":
        content.append("Result for " + state.position + ": " + state.recommendation)
    content.append(Button("Home", index))
    return Page(state, content)
 
 
@route
def run_recommendation(state: State, position: str) -> Page:
    """Save the chosen position, calculate the recommendation, and show it."""
    state.position = position
    state.recommendation = build_recommendation(state)
    return recommendation_page(state)
 
 
@route
def how_it_works(state: State) -> Page:
    """Explain how the scores are calculated."""
    return Page(state, [
        "How it works",
        "1. Form: your season average (" + str(SEASON_WEIGHT) + ") and last-3-games average ("
        + str(RECENT_WEIGHT) + ") are blended, so one lucky week does not decide everything.",
        "2. Matchup: the score is multiplied by (points the opponent allows / league average for that position).",
        "3. Home field: players at home get a " + str(HOME_BONUS) + "x boost.",
        "4. Turnovers: each fumble lost or interception per game costs " + str(TURNOVER_PENALTY) + " points.",
        "5. Injured or bye-week players are NA and are never recommended.",
        "6. The highest score at the chosen position wins; on an exact tie the first player entered wins.",
        Button("Home", index),
    ])
 
 
@route
def restart(state: State) -> Page:
    """Clear everything back to the starting sample data and return home."""
    state.players = starting_players()
    state.position = "WR"
    state.recommendation = ""
    state.error_message = ""
    return index(state)
 
set_website_title("FantasyStart/SitHelper")
set_site_information(
    author="Landis Leatherman",
    description="Recommends which fantasy football player to start using recent form, matchup, home field and turnovers.",
    sources="Thanks to my sister who is a comp sci major and the provided LLM",
    planning=["plan.pdf"],
    links=["https://github.com/LandisL/Fantasy-Start-Sit-Helpers"]
)
hide_debug_information()
set_website_framed(False)

start_server(State(starting_players(), "WR", "", ""))
 


    
    
                        
    


 
    
    




    

