import streamlit as st
import pandas as pd

# 1. Set up the web page
st.set_page_config(page_title="2026 NCAA CBB Rankings", layout="wide")
st.title("🏀 2026 CBB Predictive Rankings")
st.write("Statistically predictive rankings and H2H matchup predictor.")

# 2. Load the data
@st.cache_data
def load_data():
    kp_df = pd.read_csv('summary26.csv')
    torvik_df = pd.read_csv('2026_team_results.csv')
    
    torvik_df = torvik_df.rename(columns={'team': 'TeamName'})
    
    # NEW: Grab 'elite SOS' and 'sos' from the Torvik file too
    df = pd.merge(kp_df, torvik_df[['TeamName', 'WAB', 'ncsos', 'sos', 'elite SOS']], on='TeamName', how='left')
    
    # Fill any missing merge values to prevent math errors
    df['WAB'] = df['WAB'].fillna(0)
    df['ncsos'] = df['ncsos'].fillna(df['ncsos'].mean())
    df['sos'] = df['sos'].fillna(df['sos'].mean())
    df['elite SOS'] = df['elite SOS'].fillna(df['elite SOS'].mean())
    
    # Calculate Raw Win % 
    df['Raw Win Pct'] = (df['AdjOE']**11.5) / (df['AdjOE']**11.5 + df['AdjDE']**11.5)

    # ==========================================
    # 🧮 UPGRADED COMPOSITE POWER RANKING MATH
    # ==========================================
    win_norm = (df['Raw Win Pct'] - df['Raw Win Pct'].min()) / (df['Raw Win Pct'].max() - df['Raw Win Pct'].min())
    wab_norm = (df['WAB'] - df['WAB'].min()) / (df['WAB'].max() - df['WAB'].min())
    ncsos_norm = (df['ncsos'] - df['ncsos'].min()) / (df['ncsos'].max() - df['ncsos'].min())
    elite_norm = (df['elite SOS'] - df['elite SOS'].min()) / (df['elite SOS'].max() - df['elite SOS'].min())
    
    # 2. Create the Weighted Composite Score (55% Math, 25% WAB, 10% Elite SOS, 10% NC-SOS)
    df['Composite Score'] = (win_norm * 0.55) + (wab_norm * 0.25) + (elite_norm * 0.10) + (ncsos_norm * 0.10)
    
    # 3. Add a Numerical Ranking based on the new Composite Score
    df['Power Rank'] = df['Composite Score'].rank(ascending=False, method='min').astype(int)
    
    # ==========================================
    # 🏷️ UPGRADED TEAM PROFILING (Fraud Watch)
    # ==========================================
    def tag_team(row):
        # 1. True Contender: Elite efficiency + Proven against good teams
        if row['RankAdjOE'] <= 25 and row['RankAdjDE'] <= 25 and row['elite SOS'] >= 0.500:
            return "🏆 True Contender"
            
        # 2. Paper Tiger: Great efficiency, but played a horrible schedule
        elif (row['RankAdjOE'] <= 25 or row['RankAdjDE'] <= 25) and row['elite SOS'] < 0.450 and row['ncsos'] < 0.450:
            return "🚨 Fraud Watch - Paper Tiger"
            
        # 3. All Offense, Bad Defense
        elif row['RankAdjOE'] <= 20 and row['RankAdjDE'] > 50:
            return "🚨 Fraud Watch - All Offense"
            
        # 4. All Defense, Bad Offense
        elif row['RankAdjDE'] <= 20 and row['RankAdjOE'] > 50:
            return "🚨 Fraud Watch - All Defense"
            
        # 5. Battle-Tested Grinders: Maybe not elite statistically, but have a massive resume
        elif row['WAB'] >= 5.0 and row['elite SOS'] >= 0.600:
            return "🛡️ Battle-Tested Threat"
            
        else:
            return ""
            
    df['Team Profile'] = df.apply(tag_team, axis=1)
            
    df['Team Profile'] = df.apply(tag_team, axis=1)
    
    # Format display columns
    df['Predicted Win %'] = (df['Raw Win Pct'] * 100).round(2).astype(str) + '%'
    df['AdjEM'] = df['AdjEM'].round(2)
    df['WAB'] = df['WAB'].round(1)
    df['NC-SOS'] = df['ncsos'].round(3)
    df['Overall SOS'] = df['sos'].round(3)
    df['Elite SOS'] = df['elite SOS'].round(3)
    
    return df

df = load_data()

# ==========================================
# ⚔️ HEAD-TO-HEAD MATCHUP PREDICTOR
# ==========================================
st.header("⚔️ Matchup Predictor")

col1, col2 = st.columns(2)
team_list = sorted(df['TeamName'].tolist())

with col1:
    team_a = st.selectbox("Select Team A", team_list, index=team_list.index("Kentucky") if "Kentucky" in team_list else 0)
with col2:
    team_b = st.selectbox("Select Team B", team_list, index=team_list.index("Louisville") if "Louisville" in team_list else 1)

if team_a and team_b and team_a != team_b:
    # Get all the stats for Team A
    team_a_data = df[df['TeamName'] == team_a].iloc[0]
    pct_a = team_a_data['Raw Win Pct']
    em_a = team_a_data['AdjEM']
    tempo_a = team_a_data['AdjTempo']
    
    # Get all the stats for Team B
    team_b_data = df[df['TeamName'] == team_b].iloc[0]
    pct_b = team_b_data['Raw Win Pct']
    em_b = team_b_data['AdjEM']
    tempo_b = team_b_data['AdjTempo']
    
    # Run the Math
    prob_a = (pct_a - (pct_a * pct_b)) / (pct_a + pct_b - (2 * pct_a * pct_b))
    prob_b = 1 - prob_a
    
    expected_possessions = (tempo_a + tempo_b) / 2
    margin_per_100 = em_a - em_b
    point_spread = margin_per_100 * (expected_possessions / 100)
    
    if point_spread > 0:
        spread_text = f"**{team_a} -{abs(point_spread):.1f}**"
        winner_text = f"🏆 **{team_a}** has a **{prob_a * 100:.1f}%** chance to win."
    else:
        spread_text = f"**{team_b} -{abs(point_spread):.1f}**"
        winner_text = f"🏆 **{team_b}** has a **{prob_b * 100:.1f}%** chance to win."
    
    # Display the Result
    st.subheader("Matchup Result:")
    st.success(f"{winner_text} \n\n🏀 **Predicted Spread:** {spread_text} (Pace: {expected_possessions:.1f} possessions)")
    
   # --- NEW: TALE OF THE TAPE ---
    st.write("### 📊 Tale of the Tape")
    
    # Changed to 2 columns to remove the center labels
    tcol1, tcol2 = st.columns(2)
    
    with tcol1:
        st.markdown(f"#### {team_a}")
        st.write(f"**{team_a_data['Team Profile']}**" if team_a_data['Team Profile'] != "" else "*(No specific profile)*")
        
        # Native Streamlit metrics (Left-aligned)
        st.metric("Power Rank", f"#{team_a_data['Power Rank']}")
        st.metric("Wins Above Bubble", team_a_data['WAB'])
        st.metric("Elite SOS", team_a_data['Elite SOS'])

    with tcol2:
        # Determine the profile string for Team B
        profile_b = f"**{team_b_data['Team Profile']}**" if team_b_data['Team Profile'] != "" else "*(No specific profile)*"
        
        # Using HTML to force Team B's stats to right-align and perfectly mirror Team A
        st.markdown(f"<h4 style='text-align: right;'>{team_b}</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right;'>{profile_b}</div><br>", unsafe_allow_html=True)
        
        # Recreating the "metric" visual style, but pushed to the right
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 14px; color: gray;'>Power Rank</span><h2 style='margin-top: -5px;'>#{team_b_data['Power Rank']}</h2></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 14px; color: gray;'>Wins Above Bubble</span><h2 style='margin-top: -5px;'>{team_b_data['WAB']}</h2></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 14px; color: gray;'>Power Rank</span><h2 style='margin-top: -5px;'>#{team_b_data['Power Rank']}</h2></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 14px; color: gray;'>Wins Above Bubble</span><h2 style='margin-top: -5px;'>{team_b_data['WAB']}</h2></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right;'><span style='font-size: 14px; color: gray;'>Elite SOS</span><h2 style='margin-top: -5px;'>{team_b_data['Elite SOS']}</h2></div>", unsafe_allow_html=True)
elif team_a == team_b:
    st.warning("Please select two different teams to compare.")

st.divider()

# ==========================================
# 📊 FULL TEAM RANKINGS TABLE
# ==========================================
st.header("📊 Full Team Rankings")
st.write("**Power Rank** is a composite score weighting Efficiency (55%), Wins Above Bubble (25%), Elite SOS (10%), and Non-Con SOS (10%).")

# Select columns to show
display_df = df[['Power Rank', 'TeamName', 'Predicted Win %', 'WAB', 'Elite SOS', 'Overall SOS', 'NC-SOS', 'Team Profile']]

# Sort by Power Rank
display_df = display_df.sort_values(by='Power Rank', ascending=True)

search = st.text_input("Search for a team to filter the table:")
if search:
    display_df = display_df[display_df['TeamName'].str.contains(search, case=False)]

dynamic_height = (len(display_df) * 35) + 40

st.dataframe(
    display_df, 
    use_container_width=True,
    hide_index=True,
    height=dynamic_height
)