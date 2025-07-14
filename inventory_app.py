import streamlit as st
import pandas as pd
import os
from io import BytesIO

# ----------------------------------------------------------------------------
# Constants
SHELVES = 4  # number of shelves
LEVELS = 4   # levels per shelf
DATA_FILE = "inventory.csv"

# ----------------------------------------------------------------------------
# Helper functions

def load_inventory():
    """Load inventory from CSV file if it exists."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["item", "shelf", "level"])
    return df


def save_inventory(df: pd.DataFrame):
    """Save inventory DataFrame to CSV."""
    df.to_csv(DATA_FILE, index=False)


def add_item(df: pd.DataFrame, item: str, shelf: int, level: int) -> pd.DataFrame:
    """Add a new item to the inventory."""
    new_row = {"item": item, "shelf": shelf, "level": level}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_inventory(df)
    return df


def remove_item(df: pd.DataFrame, item: str, shelf: int, level: int) -> pd.DataFrame:
    """Remove an item from the inventory."""
    mask = ~((df["item"] == item) & (df["shelf"] == shelf) & (df["level"] == level))
    df = df[mask].reset_index(drop=True)
    save_inventory(df)
    return df


# ----------------------------------------------------------------------------
# Streamlit App

def main():
    st.set_page_config(layout="wide")
    st.title("창고 재고 관리 시스템")

    if "inventory" not in st.session_state:
        st.session_state.inventory = load_inventory()
    if "selected" not in st.session_state:
        st.session_state.selected = None  # (shelf, level)

    # Search box
    st.sidebar.header("검색")
    search_query = st.sidebar.text_input("물품명 검색")
    if st.sidebar.button("검색"):
        df = st.session_state.inventory
        res = df[df["item"].str.contains(search_query, case=False)]
        if not res.empty:
            row = res.iloc[0]
            st.sidebar.success(f"{row['item']}는 {row['shelf']}번 선반 {row['level']}층에 있습니다.")
        else:
            st.sidebar.warning("검색 결과가 없습니다.")

    st.sidebar.header("재고 전체 다운로드")
    if st.sidebar.button("Excel 다운로드"):
        df = st.session_state.inventory
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        st.sidebar.download_button(
            label="엑셀 다운로드",
            data=output.getvalue(),
            file_name="inventory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.write("## 창고 레이아웃")
    layout_cols = st.columns(SHELVES)

    for shelf in range(1, SHELVES + 1):
        with layout_cols[shelf - 1]:
            st.markdown(f"### 선반 {shelf}")
            for level in range(1, LEVELS + 1):
                btn_label = f"{level}층"
                if st.button(btn_label, key=f"{shelf}-{level}"):
                    st.session_state.selected = (shelf, level)
                # Display items count
                count = len(st.session_state.inventory[(st.session_state.inventory["shelf"] == shelf) & (st.session_state.inventory["level"] == level)])
                st.caption(f"보유 수량: {count}")

    # Selected cell operations
    if st.session_state.selected:
        shelf, level = st.session_state.selected
        st.write(f"### 선택된 위치: {shelf}번 선반 {level}층")
        df = st.session_state.inventory
        items_here = df[(df["shelf"] == shelf) & (df["level"] == level)]
        if not items_here.empty:
            st.table(items_here[["item"]])
        else:
            st.write("현재 물품이 없습니다.")

        new_item = st.text_input("추가할 물품명")
        if st.button("물품 추가") and new_item:
            st.session_state.inventory = add_item(df, new_item, shelf, level)
            st.experimental_rerun()

        if not items_here.empty:
            remove_target = st.selectbox("삭제할 물품 선택", items_here["item"].unique())
            if st.button("물품 삭제"):
                st.session_state.inventory = remove_item(df, remove_target, shelf, level)
                st.experimental_rerun()


if __name__ == "__main__":
    main()