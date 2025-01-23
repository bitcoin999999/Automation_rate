import streamlit as st
import pandas as pd

def calculate_automation_rate(data):
    df = pd.DataFrame(data)
    df["weighted_time"] = df["time"] * df["weight"]
    auto_time_sum = df[df["auto"] == True]["weighted_time"].sum()
    manual_time_sum = df[df["auto"] == False]["weighted_time"].sum()

    if (auto_time_sum + manual_time_sum) == 0:
        return 0
    else:
        return (auto_time_sum / (auto_time_sum + manual_time_sum)) * 100

def main():
    st.title("공장 자동화율 계산기")

    # 입력받을 모션 개수
    num_rows = st.number_input("모션 개수", min_value=1, value=5, step=1)

    # 사용자 입력 저장할 리스트
    motion_data = []

    for i in range(num_rows):
        st.subheader(f"모션 {i+1}")
        motion_name = st.text_input(f"모션 {i+1} 이름", value=f"motion_{i+1}", key=f"name_{i}")
        auto_select = st.selectbox(f"모션 {i+1} 자동/수동", ["자동", "수동"], key=f"auto_{i}")
        time_val = st.number_input(f"소요 시간(초)", min_value=0.0, value=10.0, step=1.0, key=f"time_{i}")
        weight_val = st.number_input(f"가중치", min_value=0.0, value=1.0, step=0.1, key=f"weight_{i}")
        
        motion_data.append({
            "motion": motion_name,
            "auto": True if auto_select == "자동" else False,
            "time": time_val,
            "weight": weight_val
        })

    if st.button("계산하기"):
        rate = calculate_automation_rate(motion_data)
        st.write(f"**자동화율:** {rate:.2f}%")

        # 그래프 보여주기
        auto_weighted_sum = sum(d["time"]*d["weight"] for d in motion_data if d["auto"])
        manual_weighted_sum = sum(d["time"]*d["weight"] for d in motion_data if not d["auto"])
        chart_data = pd.DataFrame({
            "Category": ["자동", "수동"],
            "Weighted_Time": [auto_weighted_sum, manual_weighted_sum]
        })
        st.bar_chart(chart_data.set_index("Category"))

    # 데이터 저장하기 버튼 추가
    if st.button("저장하기"):
        df_to_save = pd.DataFrame(motion_data)
        df_to_save.to_csv('automation_data.csv', mode='a', header=False, index=False)
        st.success("데이터 저장됨")

if __name__ == "__main__":
    main()

