import streamlit as st
import pandas as pd

# 1. Set up the web page
st.set_page_config(page_title="2026 NCAA CBB Rankings", layout="wide")
st.title("🏀 2026 CBB Predictive Rankings")
st.write("Statistically predictive rankings and H2H matchup predictor.")

# 2. Load the data
@st.cache_data
def load_data():
    # Reading the Excel file (as you set up earlier!)
    df = pd.read_excel('NCAA Rankings-V3.xlsx')
    
    # Calculate Raw Win % (we need the raw decimals for the matchup math)
    df['Raw Win Pct'] = (df['AdjOE']**11.5) / (df['AdjOE']**11.5 + df['AdjDE']**11.5)

    # Add a Numerical Ranking (1 to 360+) based on the Raw Win Pct
    df['Power Rank'] = df['Raw Win Pct'].rank(ascending=False, method='min').astype(int)
    
    # Calculate Team Profile
    def tag_team(row):
        if row['RankAdjOE'] <= 20 and row['RankAdjDE'] <= 20:
            return "🏆 Championship Contender"
        elif row['RankAdjOE'] <= 20 and row['RankAdjDE'] > 40:
            return "🚨 Fraud Watch - Offense"
        elif row['RankAdjDE'] <= 20 and row['RankAdjOE'] > 40:
            return "🚨 Fraud Watch - Defense"
        else:
            return ""
            
    df['Team Profile'] = df.apply(tag_team, axis=1)
    
    # Format the Display Win % as a nice percentage string
    df['Predicted Win %'] = (df['Raw Win Pct'] * 100).round(2).astype(str) + '%'
    df['AdjEM'] = df['AdjEM'].round(2)
    
    return df

df = load_data()

# ==========================================
# ⚔️ NEW: HEAD-TO-HEAD MATCHUP PREDICTOR
# ==========================================
st.header("⚔️ Matchup Predictor")

# Create two columns for the dropdown menus
col1, col2 = st.columns(2)

# Get an alphabetical list of all teams
team_list = sorted(df['TeamName'].tolist())

with col1:
    team_a = st.selectbox("Select Team A", team_list, index=team_list.index("Kentucky") if "Kentucky" in team_list else 0)
    
with col2:
    team_b = st.selectbox("Select Team B", team_list, index=team_list.index("Louisville") if "Louisville" in team_list else 1)

# Run the Math if two different teams are selected
if team_a and team_b and team_a != team_b:
    
    # 1. Get the data for both teams
    pct_a = df[df['TeamName'] == team_a]['Raw Win Pct'].values[0]
    pct_b = df[df['TeamName'] == team_b]['Raw Win Pct'].values[0]
    
    em_a = df[df['TeamName'] == team_a]['AdjEM'].values[0]
    em_b = df[df['TeamName'] == team_b]['AdjEM'].values[0]
    
    tempo_a = df[df['TeamName'] == team_a]['AdjTempo'].values[0]
    tempo_b = df[df['TeamName'] == team_b]['AdjTempo'].values[0]
    
    # 2. Log5 Formula for Win Probability
    prob_a = (pct_a - (pct_a * pct_b)) / (pct_a + pct_b - (2 * pct_a * pct_b))
    prob_b = 1 - prob_a
    
    # 3. Calculate Predicted Point Spread
    expected_possessions = (tempo_a + tempo_b) / 2
    margin_per_100 = em_a - em_b
    point_spread = margin_per_100 * (expected_possessions / 100)
    
    # Determine who is favored for the text output
    if point_spread > 0:
        spread_text = f"**{team_a} -{abs(point_spread):.1f}**"
        winner_text = f"🏆 **{team_a}** has a **{prob_a * 100:.1f}%** chance to win."
    else:
        spread_text = f"**{team_b} -{abs(point_spread):.1f}**"
        winner_text = f"🏆 **{team_b}** has a **{prob_b * 100:.1f}%** chance to win."
    
    # Display the Result!
    st.subheader("Matchup Result:")
    st.success(f"{winner_text} \n\n🏀 **Predicted Spread:** {spread_text} (Pace: {expected_possessions:.1f} possessions)")

elif team_a == team_b:
    st.warning("Please select two different teams to see a matchup.")

st.divider() # Draws a nice line across the screen

# ==========================================
# 📊 FULL TEAM RANKINGS TABLE
# ==========================================
st.header("📊 Full Team Rankings")

# Select only the columns we want to show
display_df = df[['Power Rank', 'TeamName', 'AdjEM', 'Predicted Win %', 'Team Profile']]

# Sort by Predicted Win % (highest to lowest)
display_df = display_df.sort_values(by='Power Rank', ascending=True)

# Add a search bar to look up specific teams
search = st.text_input("Search for a team to filter the table:")
if search:
    display_df = display_df[display_df['TeamName'].str.contains(search, case=False)]

# Calculate the exact height needed to show all rows (no double scrolling!)
dynamic_height = (len(display_df) * 35) + 40

# Display the interactive table on the webpage
st.dataframe(
    display_df, 
    use_container_width=True,
    hide_index=True,
    height=dynamic_height
)