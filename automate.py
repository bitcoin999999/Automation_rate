import streamlit as st
import pandas as pd
import io

# --------------------------------------------------------------------------------
# 페이지 레이아웃 설정 (좌우 넓게)
st.set_page_config(layout="wide")

# --------------------------------------------------------------------------------
# 자동화율 계산 함수
def calculate_automation_rate(motion_data):
    """
    motion_data: [{'motion': str, 'auto': bool, 'time': float, 'weight': float, 'device_id': str, 
                   'operator': str, 'remarks': str}, ...]
    """
    if not motion_data:
        return 0.0
    df = pd.DataFrame(motion_data)
    df["weighted_time"] = df["time"] * df["weight"]
    auto_time_sum = df[df["auto"] == True]["weighted_time"].sum()
    manual_time_sum = df[df["auto"] == False]["weighted_time"].sum()
    if (auto_time_sum + manual_time_sum) == 0:
        return 0.0
    else:
        return (auto_time_sum / (auto_time_sum + manual_time_sum)) * 100

# --------------------------------------------------------------------------------
# 공정별 Excel 저장 함수
def save_to_excel(data_dict, auto_rates, total_rate):
    """
    data_dict: {
      '완분': [{'motion':..., 'auto':..., 'time':..., 'weight':..., 
                'device_id':..., 'operator':..., 'remarks':...}, ...],
      '프레스': [...], ...
    }
    auto_rates: {'완분': 45.0, '프레스': 50.0, ...}
    total_rate: (float) 전체 평균 자동화율
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1) 공정별 raw data 시트 생성
        for process_name, motions in data_dict.items():
            if len(motions) == 0:
                # 모션이 없는 공정은 빈 DF
                df_process = pd.DataFrame({"motion": [], "auto": [], "time": [], "weight": [],
                                           "device_id": [], "operator": [], "remarks": []})
            else:
                df_process = pd.DataFrame(motions)
            df_process.to_excel(writer, sheet_name=process_name, index=False)
        
        # 2) Summary 시트에 공정별 자동화율 + TOTAL 정리
        summary_data = []
        for k, v in auto_rates.items():
            summary_data.append({"공정명": k, "자동화율(%)": v})
        # 총평 행 추가
        summary_data.append({"공정명": "TOTAL", "자동화율(%)": total_rate})

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    
    return output.getvalue()

# --------------------------------------------------------------------------------
def main():
    st.title("공정별 자동화율 계산기")
    st.caption("Created by 설비관리팀 정인수")
    tab_names = ["완분", "프레스", "코팅", "연삭", "세척", "검사"]

    # 탭 생성
    tabs = st.tabs(tab_names)
    
    # 공정별 데이터를 담을 딕셔너리
    data_dict = {}

    # -- 기본적으로 session_state에 계산 결과 저장용 키 초기화 --
    if "calculated" not in st.session_state:
        st.session_state.calculated = False
    if "auto_rates" not in st.session_state:
        st.session_state.auto_rates = {}
    if "total_rate" not in st.session_state:
        st.session_state.total_rate = 0.0
    if "data_dict" not in st.session_state:
        st.session_state.data_dict = {}

    # --------------------------------------------------------------------------------
    # 1) 탭별 데이터 입력 (2개 컬럼으로 입력 필드를 나눔)
    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            st.subheader(f"[{tab_name}] 공정 데이터 입력")
            num_rows = st.number_input(
                f"{tab_name} 모션 개수", min_value=0, value=1, step=1, key=f"{tab_name}_num_rows"
            )
            
            motions = []
            for j in range(num_rows):
                # 왼쪽 입력(4개), 오른쪽 입력(3개)
                col1, col2 = st.columns(2)
                
                with col1:
                    motion_name = st.text_input(f"{tab_name} 모션 {j+1} 이름", 
                                                value=f"{tab_name}_motion_{j+1}", 
                                                key=f"{tab_name}_motion_name_{j}")
                    auto_select = st.selectbox(f"{tab_name} 모션 {j+1} 자동/수동", 
                                               ["자동", "수동"], 
                                               key=f"{tab_name}_auto_{j}")
                    time_val = st.number_input(f"{tab_name} 소요 시간(초)", 
                                               min_value=0.0, 
                                               value=10.0, 
                                               step=1.0, 
                                               key=f"{tab_name}_time_{j}")
                    weight_val = st.number_input(f"{tab_name} 가중치", 
                                                 min_value=0.0, 
                                                 value=1.0, 
                                                 step=0.1, 
                                                 key=f"{tab_name}_weight_{j}")
                
                with col2:
                    device_id = st.text_input(f"{tab_name} 모션 {j+1} 설비명", 
                                              value="", 
                                              key=f"{tab_name}_device_id_{j}")
                    operator = st.text_input(f"{tab_name} 모션 {j+1} 설비 MAKER", 
                                             value="", 
                                             key=f"{tab_name}_operator_{j}")
                    remarks = st.text_input(f"{tab_name} 모션 {j+1} 비고", 
                                            value="", 
                                            key=f"{tab_name}_remarks_{j}")

                # motions 리스트에 모두 추가
                motions.append({
                    "motion": motion_name,
                    "auto": True if auto_select == "자동" else False,
                    "time": time_val,
                    "weight": weight_val,
                    "device_id": device_id,
                    "operator": operator,
                    "remarks": remarks
                })
            
            data_dict[tab_name] = motions

    # --------------------------------------------------------------------------------
    # 2) 계산 버튼 & 저장 버튼 (각각 별도 컬럼)
    calc_col, save_col = st.columns(2)
    calc_btn = calc_col.button("총 계산하기")
    save_btn = save_col.button("저장하기")

    # --------------------------------------------------------------------------------
    # (A) 계산하기 버튼 누르면 공정별 자동화율 + TOTAL 계산 후 session_state에 저장
    if calc_btn:
        auto_rates = {}
        for process_name, motions in data_dict.items():
            rate = calculate_automation_rate(motions)
            auto_rates[process_name] = rate
        
        # 전체 평균 자동화율
        if len(auto_rates) > 0:
            total_rate = sum(auto_rates.values()) / len(auto_rates)
        else:
            total_rate = 0.0

        st.session_state.auto_rates = auto_rates
        st.session_state.total_rate = total_rate
        st.session_state.data_dict = data_dict
        st.session_state.calculated = True

    # --------------------------------------------------------------------------------
    # (B) 계산 결과가 있는 경우에만 화면 표시
    if st.session_state.calculated:
        st.write("## 공정별 자동화율 결과")
        for k, v in st.session_state.auto_rates.items():
            st.write(f"- **{k}**: {v:.2f}%")
        st.write(f"### TOTAL 자동화율: {st.session_state.total_rate:.2f}%")

        # 간단 바 차트
        chart_df = pd.DataFrame({
            "공정명": list(st.session_state.auto_rates.keys()),
            "자동화율(%)": list(st.session_state.auto_rates.values())
        })
        st.bar_chart(chart_df.set_index("공정명"))

    # --------------------------------------------------------------------------------
    # (C) "저장하기" 버튼 누르면 엑셀 데이터 생성 후 다운로드 버튼 표시
    if save_btn and st.session_state.calculated:
        excel_data = save_to_excel(
            st.session_state.data_dict, 
            st.session_state.auto_rates, 
            st.session_state.total_rate
        )
        
        st.download_button(
            label="엑셀 다운로드",
            data=excel_data,
            file_name="automation_rate.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
