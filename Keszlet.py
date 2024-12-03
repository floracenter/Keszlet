import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# Árfolyam
EURO_TO_LEI = 5  # 1 euró = 5 lej

# Adatbázis csatlakozás
conn = sqlite3.connect('keszlet.db')
cursor = conn.cursor()

# Táblázat adatok lekérése
def frissit_lista():
    cursor.execute("SELECT id, nev, keszlet, eltarthatosag, erkezes_datum, beszerzesi_ar, eladasi_ar_kotes, eladasi_ar_doboz, kod FROM viragok")
    rows = cursor.fetchall()

    table_data = []
    for row in rows:
        lejarati_datum = datetime.strptime(row[4], '%Y-%m-%d') + timedelta(days=row[3])
        hatralevo_napok = (lejarati_datum - datetime.now()).days
        szazalek = (hatralevo_napok / row[3]) * 100 if row[3] > 0 else 0

        if szazalek > 50:
            szin = "Zöld"
        elif 25 <= szazalek <= 50:
            szin = "Sárga"
        else:
            szin = "Piros"

        profit_kotes = row[6] - row[5] if row[5] and row[6] else None
        profit_doboz = row[7] - row[5] if row[5] and row[7] else None

        table_data.append({
            "ID": row[0],
            "Név": row[1],
            "Készlet": row[2],
            "Eltarthatóság (nap)": row[3],
            "Hátralévő napok": hatralevo_napok,
            "Beszerzési Ár": round(row[5], 2) if row[5] else None,
            "Eladási Ár (kötés)": round(row[6], 2) if row[6] else None,
            "Eladási Ár (doboz)": round(row[7], 2) if row[7] else None,
            "Kód": row[8],
            "Profit (kötés)": profit_kotes,
            "Profit (doboz)": profit_doboz,
            "Frissesség": szin
        })

    return pd.DataFrame(table_data)

# CSS stílus a mobilbarát designhoz
st.markdown("""
    <style>
    .css-18e3th9 {
        padding: 0;  /* Csökkenti a margót */
    }
    .css-1d391kg {
        max-width: 100%;  /* Szélességet teljes kijelzőhöz igazítja */
    }
    .sidebar-content {
        padding: 1rem;  /* Kényelmesebb oldalmenü */
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("Készletkezelő")
st.sidebar.header("Új virág hozzáadása")

# Virág hozzáadás form
with st.sidebar.form("add_flower_form"):
    nev = st.text_input("Virág neve")
    keszlet = st.number_input("Készlet", min_value=0, step=1)
    eltarthatosag = st.number_input("Eltarthatóság (nap)", min_value=0, step=1)
    beszerzesi_ar = st.number_input("Beszerzési ár", min_value=0.0, step=0.01)
    eladasi_ar_kotes = st.number_input("Eladási ár (kötés)", min_value=0.0, step=0.01)
    eladasi_ar_doboz = st.number_input("Eladási ár (doboz)", min_value=0.0, step=0.01)
    valuta = st.selectbox("Valuta", ["EUR", "LEI"])
    tva = st.slider("TVA (%)", 0, 25, 19)

    if st.form_submit_button("Hozzáadás"):
        erkezes_datum = datetime.now().strftime('%Y-%m-%d')
        beszerzesi_ar = beszerzesi_ar * EURO_TO_LEI if valuta == "EUR" else beszerzesi_ar
        beszerzesi_ar *= (1 + tva / 100)

        cursor.execute(
            "INSERT INTO viragok (nev, keszlet, eltarthatosag, erkezes_datum, beszerzesi_ar, eladasi_ar_kotes, eladasi_ar_doboz) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (nev, keszlet, eltarthatosag, erkezes_datum, beszerzesi_ar, eladasi_ar_kotes, eladasi_ar_doboz)
        )
        conn.commit()
        st.success("Virág sikeresen hozzáadva!")

# Táblázat megjelenítése
st.header("Virágok listája")
viragok = frissit_lista()

if not viragok.empty:
    def highlight_frissesseg(row):
        color = {"Zöld": "#d4edda", "Sárga": "#fff3cd", "Piros": "#f8d7da"}.get(row["Frissesség"], "white")
        return [f"background-color: {color}"] * len(row)

    styled_table = viragok.style.apply(highlight_frissesseg, axis=1)
    st.write(styled_table.to_html(), unsafe_allow_html=True, use_container_width=True)
else:
    st.write("Nincs elérhető adat.")
