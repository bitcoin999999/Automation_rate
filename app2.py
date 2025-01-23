import streamlit as st
import pandas as pd
import io

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

    # 모션 개수 입력
    num_rows = st.number_input("모션 개수", min_value=1, value=5, step=1)

    motion_data = []

    # 모션 정보 입력
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

        # 그래프 그리기
        auto_weighted_sum = sum(d["time"]*d["weight"] for d in motion_data if d["auto"])
        manual_weighted_sum = sum(d["time"]*d["weight"] for d in motion_data if not d["auto"])
        chart_data = pd.DataFrame({
            "Category": ["자동", "수동"],
            "Weighted_Time": [auto_weighted_sum, manual_weighted_sum]
        })
        st.bar_chart(chart_data.set_index("Category"))

    # 다운로드 버튼 (CSV, Excel)
    # "저장하기" 누르면 데이터프레임 생성 후, 다운로드 옵션 제공
    if st.button("저장하기"):
        df_to_save = pd.DataFrame(motion_data)

        # CSV 변환
        csv_data = df_to_save.to_csv(index=False, encoding='utf-8-sig')

        # Excel 변환
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_to_save.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_data = output.getvalue()

        st.write("원하는 형식을 선택해서 다운로드할 수 있엉:")

        # CSV 다운로드 버튼
        st.download_button(
            label="CSV 다운로드",
            data=csv_data,
            file_name="automation_data.csv",
            mime="text/csv"
        )

        # Excel 다운로드 버튼
        st.download_button(
            label="Excel 다운로드",
            data=excel_data,
            file_name="automation_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
