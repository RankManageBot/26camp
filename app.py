import streamlit as st
import numpy as np
import pandas as pd
from openai import OpenAI
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="2028 대입 5등급제 내신 환산 & AI 컨설턴트",
    page_icon="🎯",
    layout="wide"
)

# 2. 모던 스타일 CSS 적용
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 세팅 */
    .main {
        background-color: #f8f9fa;
    }
    
    /* 카드 스타일 카드 컨테이너 */
    .css-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }

    /* 메트릭 카드 스타일 */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 15px;
    }
    .metric-card {
        background: #f1f3f5;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        flex: 1;
        border: 1px solid #e9ecef;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #495057;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1971c2;
    }
    </style>
""", unsafe_allow_html=True)

# 헤더 타이틀
st.title("🎯 2028 대입 개편안 맞춤 5등급제 성적 환산 & AI 진학 컨설턴트")
st.caption("2022 개정 교육과정을 반영한 정밀 내신 환산과 Upstage Solar AI 맞춤 입시 리포트를 한눈에 확인하세요.")
st.divider()

# API 키 세팅
api_key = "up_Y7OKHBUB2q7pi7C4E1ILIWItBAUOG"

# 학기 목록 상수
SEMESTERS = ["1학년 1학기", "1학년 2학기", "2학년 1학기", "2학년 2학기", "3학년 1학기", "3학년 2학기"]

# 과목 데이터베이스
SUBJECTS_DB = {
    "공통": {
        "국어": ["공통국어1", "공통국어2"],
        "수학": ["공통수학1", "공통수학2", "기본수학1", "기본수학2"],
        "영어": ["공통영어1", "공통영어2", "기본영어1", "기본영어2"],
        "한국사/사회": ["한국사1", "한국사2", "통합사회1", "통합사회2"],
        "과학": ["통합과학1", "통합과학2", "과학탐구실험1", "과학탐구실험2"]
    },
    "일반선택": {
        "국어": ["화법과 언어", "독서와 작문", "문학"],
        "수학": ["대수", "미적분Ⅰ", "확률과 통계"],
        "영어": ["영어Ⅰ", "영어Ⅱ", "영어 독해와 작문"],
        "한국사/사회": ["세계시민과 지리", "세계사", "사회와 문화", "현대 사회와 윤리"],
        "과학": ["물리학", "화학", "생명과학", "지구과학"],
        "정보": ["정보"],
        "제2외국어": ["일본어", "중국어"]
    },
    "진로선택": {
        "국어": ["주제 탐구 독서", "문학과 영상", "직무 의사소통"],
        "수학": ["미적분Ⅱ", "기하", "경제 수학", "인공지능 수학", "직무 수학"],
        "영어": ["직무 영어", "영어 발표와 토론", "심화 영어", "영미 문학 읽기", "심화 영어 독해와 작문"],
        "한국사/사회": ["인문학과 윤리", "동아시아 역사 기행", "정치", "경제", "윤리와 사상", "도시의 미래 탐구", "한국지리 탐구", "국제 관계의 이해", "법과 사회"],
        "과학": ["역학과 에너지", "전자기와 양자", "물질과 에너지", "화학 반응의 세계", "세포와 물질대사", "생물의 유전", "지구시스템과학", "행성우주과학"],
        "정보": ["인공지능 기초", "데이터 과학"],
        "제2외국어": ["심화 일본어", "심화 중국어", "일본어 회화", "중국어 회화"]
    },
    "융합선택": {
        "국어": ["독서 토론과 글쓰기", "매체 의사소통", "언어생활 탐구"],
        "수학": ["수학과 문화", "실용 수학", "수학과제 탐구"],
        "영어": ["실생활 영어 회화", "미디어 영어", "세계 문화와 영어"],
        "한국사/사회": ["여행지리", "사회문제 탐구", "금융과 경제 생활", "기후변화와 지속가능한 세계", "윤리문제 탐구", "역사로 탐구하는 현대세계"],
        "과학": ["과학과 사회", "기후변화와 환경", "융합과학 탐구"],
        "정보": ["소프트웨어와 생활"],
        "제2외국어": ["일본 문화", "중국 문화"]
    },
}

# 세션 상태 초기화
if "subjects_data" not in st.session_state:
    st.session_state["subjects_data"] = []

if "sel_category" not in st.session_state:
    st.session_state["sel_category"] = "공통"

if "sel_group" not in st.session_state:
    st.session_state["sel_group"] = "국어"

def on_category_change():
    category = st.session_state["sel_category"]
    available_groups = list(SUBJECTS_DB[category].keys())
    st.session_state["sel_group"] = available_groups[0]

# ---------------------------------------------------------
# 3. 레이아웃 2분할 (좌측: 입력 / 우측: 분석 및 AI 결과)
# ---------------------------------------------------------
left_col, right_col = st.columns([1, 1], gap="large")

# =========================================================
# [LEFT COLUMN] 성적 및 기본 정보 입력 영역
# =========================================================
with left_col:
    st.subheader("📋 성적 및 학생 정보 입력")
    
    # 기본 설정 섹션
    with st.expander("⚙️ 학생 정보 및 목표 설정", expanded=True):
        student_type = st.radio(
            "현재 학생 신분",
            ["고등학교 재학생", "자퇴생 / 검정고시 준비생"],
            index=0,
            horizontal=True
        )
        target_univ = st.text_input(
            "목표 대학 및 학과",
            value="연세대학교 컴퓨터공학과"
        )
        user_context = st.text_area(
            "추가 제출 상황 (선택)",
            placeholder="예: 공학 계열 희망 / 과학 융합선택 과목 위주 수강 중",
            height=80
        )

    # 성적 입력 섹션
    st.markdown("#### ➕ 과목 성적 추가")
    
    f_col0, f_col1, f_col2 = st.columns([1.2, 1, 1])
    with f_col0:
        semester = st.selectbox(
            "학기 선택",
            options=SEMESTERS,
            key="sel_semester"
        )
    with f_col1:
        category = st.selectbox(
            "교과 구분",
            options=list(SUBJECTS_DB.keys()),
            key="sel_category",
            on_change=on_category_change
        )
    with f_col2:
        group_options = list(SUBJECTS_DB[category].keys())
        group = st.selectbox(
            "교과군",
            options=group_options,
            key="sel_group"
        )

    f_col3, f_col4 = st.columns([3, 2])
    with f_col3:
        subject_options = SUBJECTS_DB[category][group]
        subject_name = st.selectbox(
            "과목 선택 (22개정)",
            options=subject_options,
            key="sel_subject_name"
        )
    with f_col4:
        unit = st.number_input("단위수(학점)", min_value=1, max_value=8, value=4, step=1, key="sel_unit")

    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        grade = st.number_input("석차등급", min_value=1.0, max_value=5.0, value=2.0, step=0.1, format="%.1f")
    with s_col2:
        raw_score = st.number_input("원점수", min_value=0, max_value=100, value=90, step=1)
    with s_col3:
        students_count = st.number_input("수강자수", min_value=1, value=180, step=1)
    with s_col4:
        achievement = st.selectbox("성취도", ["A", "B", "C", "D", "E"], index=0)

    st.caption("성취도별 분포비율 (%)")
    d_col1, d_col2, d_col3, d_col4, d_col5 = st.columns(5)
    with d_col1:
        dist_a = st.number_input("A (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0, format="%.1f")
    with d_col2:
        dist_b = st.number_input("B (%)", min_value=0.0, max_value=100.0, value=30.0, step=1.0, format="%.1f")
    with d_col3:
        dist_c = st.number_input("C (%)", min_value=0.0, max_value=100.0, value=30.0, step=1.0, format="%.1f")
    with d_col4:
        dist_d = st.number_input("D (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, format="%.1f")
    with d_col5:
        dist_e = st.number_input("E (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, format="%.1f")

    if st.button("➕ 과목 성적 추가", type="primary", use_container_width=True):
        dist_ratio_str = f"A:{dist_a:.1f}%, B:{dist_b:.1f}%, C:{dist_c:.1f}%, D:{dist_d:.1f}%, E:{dist_e:.1f}%"
        new_item = {
            "학기": semester,
            "교과구분": category,
            "교과군": group,
            "과목명": subject_name,
            "단위수(학점)": unit,
            "석차등급(1~5)": float(grade),
            "원점수": int(raw_score),
            "수강자수": int(students_count),
            "성취도": achievement,
            "A비율(%)": float(dist_a),
            "B비율(%)": float(dist_b),
            "C비율(%)": float(dist_c),
            "D비율(%)": float(dist_d),
            "E비율(%)": float(dist_e),
            "성취도 분포비율": dist_ratio_str
        }
        st.session_state["subjects_data"].append(new_item)
        st.success(f"[{semester}] '{subject_name}' 과목이 추가되었습니다.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📝 등록된 과목 목록")
    df_current = pd.DataFrame(st.session_state["subjects_data"])

    column_config = {
        "학기": st.column_config.SelectboxColumn("학기", options=SEMESTERS, required=True),
        "교과구분": st.column_config.SelectboxColumn("구분", options=list(SUBJECTS_DB.keys()), required=True),
        "교과군": st.column_config.TextColumn("교과군", required=True),
        "과목명": st.column_config.TextColumn("과목명", required=True),
        "단위수(학점)": st.column_config.NumberColumn("학점", min_value=1, max_value=8, step=1, required=True),
        "석차등급(1~5)": st.column_config.NumberColumn("등급", min_value=1.0, max_value=5.0, step=0.1, required=True),
        "원점수": st.column_config.NumberColumn("원점수", min_value=0, max_value=100, step=1, required=True),
        "성취도": st.column_config.SelectboxColumn("성취도", options=["A", "B", "C", "D", "E"], required=True),
    }

    edited_df = st.data_editor(
        df_current,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="editable_subject_table"
    )

    if not edited_df.empty:
        for idx, row in edited_df.iterrows():
            edited_df.at[idx, "성취도 분포비율"] = (
                f"A:{row['A비율(%)']:.1f}%, B:{row['B비율(%)']:.1f}%, C:{row['C비율(%)']:.1f}%, D:{row['D비율(%)']:.1f}%, E:{row['E비율(%)']:.1f}%"
            )
    st.session_state["subjects_data"] = edited_df.to_dict("records")


# =========================================================
# [RIGHT COLUMN] 성적 환산 통계 및 AI 컨설팅 리포트 영역
# =========================================================
with right_col:
    st.subheader("📊 환산 결과 및 AI 진학 컨설팅")

    if edited_df.empty or edited_df["단위수(학점)"].sum() == 0:
        st.info("👈 좌측에서 성적 정보를 입력하시면 실시간 환산 결과와 AI 분석을 확인하실 수 있습니다.")
    else:
        # 1. 누적 전체 성적 계산
        total_units = int(edited_df["단위수(학점)"].sum())
        weighted_grade_sum = (edited_df["석차등급(1~5)"] * edited_df["단위수(학점)"]).sum()
        avg_5grade = weighted_grade_sum / total_units

        weighted_score_sum = (edited_df["원점수"] * edited_df["단위수(학점)"]).sum()
        avg_raw_score = weighted_score_sum / total_units

        x_5scale = [1.0, 1.5, 2.5, 3.5, 4.5, 5.0]
        y_9scale = [1.0, 1.9, 3.7, 5.3, 7.5, 9.0]
        pct_scale = [0.0, 10.0, 34.0, 66.0, 90.0, 100.0]

        estimated_9grade = float(np.interp(avg_5grade, x_5scale, y_9scale))
        estimated_pct = float(np.interp(avg_5grade, x_5scale, pct_scale))

        # 메트릭 카드 UI 시각화
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-label">총 이수학점</div>
                <div class="metric-value">{total_units} 학점</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">5등급제 평균</div>
                <div class="metric-value">{avg_5grade:.2f} 등급</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">추정 9등급 환산</div>
                <div class="metric-value">{estimated_9grade:.2f} 등급</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">추정 누적 백분위</div>
                <div class="metric-value">상위 {estimated_pct:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # [NEW 1] 학기별 Radio 선택 & 알록달록 교과군 분석 막대그래프
        # ---------------------------------------------------------
        st.markdown("### 📊 학기별 교과군 분석 그래프")
        
        selected_sem = st.radio(
            "분석할 학기를 선택하세요",
            options=["전체"] + SEMESTERS,
            horizontal=True,
            key="radio_sem_analysis"
        )

        # 필터링
        if selected_sem == "전체":
            filtered_df = edited_df.copy()
        else:
            filtered_df = edited_df[edited_df["학기"] == selected_sem]

        if filtered_df.empty:
            st.warning(f"'{selected_sem}'에 입력된 과목 데이터가 없습니다.")
        else:
            # 교과군별 평균 등급 계산
            grp_data = []
            for grp, group_df in filtered_df.groupby("교과군"):
                g_units = group_df["단위수(학점)"].sum()
                if g_units > 0:
                    g_avg = (group_df["석차등급(1~5)"] * group_df["단위수(학점)"]).sum() / g_units
                    grp_data.append({"교과군": grp, "평균등급": round(g_avg, 2), "이수학점": int(g_units)})
            
            df_grp = pd.DataFrame(grp_data)

            if not df_grp.empty:
                # 알록달록한 막대그래프 생성
                fig_bar = px.bar(
                    df_grp,
                    x="교과군",
                    y="평균등급",
                    color="교과군",
                    text="평균등급",
                    title=f"<b>[{selected_sem}] 교과군별 평균 등급 (1등급에 가까울수록 우수)</b>",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_bar.update_traces(
                    texttemplate='%{text:.2f}등급',
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>평균 등급: %{y:.2f}등급<br>이수 학점: %{customdata[0]}학점<extra></extra>',
                    customdata=df_grp[["이수학점"]]
                )
                # 등급 그래프이므로 Y축 반전 (1등급이 상단)
                fig_bar.update_layout(
                    yaxis=dict(autorange="reversed", range=[5.5, 0.5], title="평균 등급 (낮을수록 좋음)"),
                    xaxis_title="교과군",
                    height=350,
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # [NEW 2] 학기별/교과군별 성적 변화 추이 꺾은선 그래프
        # ---------------------------------------------------------
        st.markdown("### 📈 학기별 성적 변화 추이 그래프")

        # 학기 순서대로 정렬하기 위해 Categorical 세팅
        trend_df = edited_df.copy()
        trend_df["학기"] = pd.Categorical(trend_df["학기"], categories=SEMESTERS, ordered=True)
        trend_df = trend_df.sort_values("학기")

        # 학기별 전체 평균 등급
        sem_trend = []
        for sem_name, sem_group in trend_df.groupby("학기", observed=False):
            s_units = sem_group["단위수(학점)"].sum()
            if s_units > 0:
                s_avg = (sem_group["석차등급(1~5)"] * sem_group["단위수(학점)"]).sum() / s_units
                sem_trend.append({"학기": sem_name, "구분": "전체 평균", "평균등급": round(s_avg, 2)})
            
            # 주요 교과군별 추이도 함께 계산
            for grp_name in ["국어", "수학", "영어", "한국사/사회", "과학"]:
                grp_sub = sem_group[sem_group["교과군"] == grp_name]
                g_units = grp_sub["단위수(학점)"].sum()
                if g_units > 0:
                    g_avg = (grp_sub["석차등급(1~5)"] * grp_sub["단위수(학점)"]).sum() / g_units
                    sem_trend.append({"학기": sem_name, "구분": grp_name, "평균등급": round(g_avg, 2)})

        df_trend = pd.DataFrame(sem_trend)

        if df_trend.empty:
            st.info("성적 추이를 표시할 학기 데이터가 부족합니다.")
        else:
            fig_line = px.line(
                df_trend,
                x="학기",
                y="평균등급",
                color="구분",
                markers=True,
                title="<b>학기 흐름에 따른 성적 변화 (꺾은선)</b>",
                color_discrete_map={
                    "전체 평균": "#FF4B4B",
                    "국어": "#6366F1",
                    "수학": "#00C9A7",
                    "영어": "#FFC75F",
                    "한국사/사회": "#845EC2",
                    "과학": "#FF9671"
                }
            )
            fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_line.update_layout(
                yaxis=dict(autorange="reversed", range=[5.5, 0.5], title="평균 등급"),
                xaxis_title="학기",
                height=380,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # AI 분석 리포트 생성 버튼
        # ---------------------------------------------------------
        if st.button("✨ Upstage Solar AI 2028 맞춤 분석 리포트 생성", type="primary", use_container_width=True):
            if not api_key:
                st.error("⚠️ API 키가 설정되지 않았습니다.")
            else:
                with st.spinner("Solar AI가 2028 모집요강 및 과목 이수 현황을 다각도로 분석 중입니다..."):
                    try:
                        client = OpenAI(
                            api_key=api_key,
                            base_url="https://api.upstage.ai/v1/solar"
                        )

                        if student_type == "고등학교 재학생":
                            type_guideline = """
                            - 고등학교 재학생 전략:
                              1) 2022 개정 교육과정 교과 이수 현황과 전공 연계 적합성 평가
                              2) 내신 5등급제 체제에서 단위수 관리, 성취도(A~E) 및 원점수/수강자수 변별력 평가 대응
                              3) 학생부 종합전형(세특, 교과 이수 충실도) 및 수시/정시 대비 방향
                            """
                        else:
                            type_guideline = """
                            - 자퇴생 / 검정고시 준비생 전략:
                              1) 검정고시 고득점 체계 및 대학별 환산 등급 대응
                              2) 2028 대입 개편안 하 청소년 생활기록부 대체서식 작성법 및 정시 준비 방향
                              3) 대학별 지원 자격 및 수능 최저학력기준 충족 전략
                            """

                        subjects_summary_str = edited_df.to_string(index=False)

                        prompt = f"""
                        너는 2028 대입 개편안 및 대한민국 주요 대학 모집요강 변화에 정통한 최상위 대입 전문 입시 컨설턴트야.

                        [학생 정보]
                        - 학생 신분: {student_type}
                        - 목표 대학 및 학과: {target_univ}
                        - 총 이수 학점(단위수): {total_units} 학점
                        - 5등급제 가중 평균 등급: {avg_5grade:.2f} 등급
                        - 기존 9등급제 추정 환산: {estimated_9grade:.2f} 등급 (상위 약 {estimated_pct:.1f}%)
                        - 가중 평균 원점수: {avg_raw_score:.1f}점
                        - 학생 추가 설명: {user_context if user_context else '특별한 추가 설명 없음'}

                        [상세 과목별 내신 성적표 (학기 포함)]
                        {subjects_summary_str}

                        [신분별 맞춤 가이드라인]
                        {type_guideline}

                        [요청 사항]
                        1. **2028 대입 관점 성적 위치 분석**: 목표 대학 기준 내신 평가 해석.
                        2. **2022 개정 과목 이수 적합성 분석**: 선택 과목 이수 현황과 전공 권장 과목 부합도.
                        3. **합격 목표 등급 & 격차 가이드**: 권장 목표 등급 및 현 성적 대비 가이드.
                        4. **맞춤형 실행 전략 3가지**: 신분과 개편안을 고려한 구체적 전략.
                        5. **따뜻한 응원 메시지**: 격려 인사로 마무리.
                        """

                        response = client.chat.completions.create(
                            model="solar-pro",
                            messages=[
                                {"role": "system", "content": "너는 대한민국 최상위 대입 입시 컨설턴트 솔라(Solar)야."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7
                        )

                        result_text = response.choices[0].message.content

                        st.markdown("### 🤖 Solar AI 맞춤 컨설팅 리포트")
                        st.markdown(result_text)

                    except Exception as e:
                        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
