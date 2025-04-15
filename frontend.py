import streamlit as st
import pandas as pd
import requests
from datetime import date

IEP1_URL = "https://eep-503n.up.railway.app/get-player-count"
IEP2_URL = "https://eep-503n.up.railway.app/get-recommendations"


game_data = pd.read_csv("game_library_data.csv") 
game_data = game_data[["name", "game_id"]]  
game_data = game_data.sort_values(by="name")

st.set_page_config(page_title="Game System", layout="centered")

st.markdown("<h1 style='text-align: center;'>🎮 Game System 🎮</h1>", unsafe_allow_html=True)

st.markdown("---")

st.title("Model 1 - Player Count Predictor")

selected_date = st.date_input("Select a date", value=date.today())

if st.button("Submit"):
    formatted_date = selected_date.isoformat() 
    payload = {"date": formatted_date}
    print("payload:", payload)

    try:
        response = requests.post(IEP1_URL, json=payload)
        response.raise_for_status()
        predicted_count = response.json()  
        print("result:", predicted_count)
        st.markdown(f"### Predicted player count for **{formatted_date}**: **{predicted_count['player_count']}**")
    except Exception as e:
        st.error(f"Error sending data: {e}")

st.markdown("---")

st.title("Model 2 - Game Recommender")

game_options = game_data["name"].tolist()

if "model1_rows" not in st.session_state:
    st.session_state.model1_rows = [{"game": "", "hours": 0}]
if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

if st.button("Add another game"):
    st.session_state.model1_rows.append({"game": "", "hours": 0})

for i in range(len(st.session_state.model1_rows)):
    cols = st.columns([2, 2, 0.5]) 

    selected_games_other = [
        row["game"] for j, row in enumerate(st.session_state.model1_rows)
        if j != i and row["game"]
    ]
    available_options = [g for g in game_options if g not in selected_games_other]

    selected_game = cols[0].selectbox(
        f"Select Game {i+1}",
        options=["Select a game"] + available_options,  
        index=(available_options.index(st.session_state.model1_rows[i]["game"]) + 1
               if st.session_state.model1_rows[i]["game"] in available_options else 0),
        key=f"game_{i}"
    )

    hours_played = cols[1].number_input(
        f"Hours Played {i+1}",
        min_value=0,
        value=st.session_state.model1_rows[i]["hours"],
        key=f"hours_{i}"
    )

    st.session_state.model1_rows[i]["game"] = selected_game
    st.session_state.model1_rows[i]["hours"] = hours_played

    if len(st.session_state.model1_rows) > 1:
        if cols[2].button("🗑️", key=f"delete_{i}"):
            st.session_state.delete_index = i

if st.session_state.delete_index is not None:
    del st.session_state.model1_rows[st.session_state.delete_index]
    st.session_state.delete_index = None
    st.rerun()  

def is_submission_valid():
    return all(row["game"] != "Select a game" for row in st.session_state.model1_rows)

def get_game_id(game_name):
    game_row = game_data[game_data["name"] == game_name]
    return str(game_row["game_id"].values[0]) if not game_row.empty else None

if st.button("Submit to Model 2", disabled=not is_submission_valid()):
    payload = {
        get_game_id(row["game"]): row["hours"]
        for row in st.session_state.model1_rows
        if row["game"] and row["game"] != "Select a game"  
    }
    print("payload:", payload)

    try:
        response = requests.post(IEP2_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        print("result:", result)

        for rec in result['recommendations']:
            with st.container():
                st.markdown(f"## **{rec['name']}**")
                
                info_cols = st.columns(2)
                info_cols[0].markdown(f"**Price:** ${rec['price']}")
                info_cols[1].markdown(f"**Rating Ratio:** {rec['rating_ratio']}")
                
                st.markdown(f"**Genres:** {', '.join(rec.get('genres', []))}")
                st.markdown(f"**Tags:** {', '.join(rec.get('tags', []))}")
                
                st.markdown("---")

    except Exception as e:
        st.error(f"Error sending data: {e}")