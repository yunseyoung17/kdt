import streamlit as st
import openpyxl
import os
# 줄바꿈 폰트유지: \n ###
# 줄바꾸고 폰트 작게 \n 
# --- 1. Excel 로드 함수 (이전과 동일) ---
BASE_PATH = os.path.dirname(__file__) + '/'
FILE_PATH = BASE_PATH + "/game_data.xlsx"
IMAGE_PATH = BASE_PATH + "images/"

def load_episodes_from_excel(filepath):
    episodes_db = {}
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        # 반복문 돌려서 A,B열 값 딕셔너리에 넣는작업
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]: break
            episode_id = str(row[0])
            dialogue_id = str(row[1])
            if episode_id not in episodes_db:
                episodes_db[episode_id] = {}
            
            choices_dict = {} # 텍스트 키로 호갑도 찾는 딕셔너리
            for i in range(4, len(row), 3):
                if row[i] is None: break
                if row[i+1] is None:
                    choices_dict[row[i]] = [0, row[i+2]]
                else:
                    choices_dict[row[i]] = [int(row[i+1]), row[i+2]]
            
            if row[3] is None:
                episodes_db[episode_id][dialogue_id] = {
                "text": row[2].replace("\\n", "\n"),
                "question": "",
                "choices": choices_dict
            }
            else:
                episodes_db[episode_id][dialogue_id] = {
                    "text": row[2].replace("\\n", "\n"),
                    "question": row[3],
                    "choices": choices_dict
                }
                # "image" : row[4] # 선택지에 따라서 점프 맨 끝자락 점프 투 열 추가 
            
        return episodes_db
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Excel 파일 로드 중 오류 발생: {e}")
        return None

# --- 2. 게임 초기화 함수 (수정됨) ---
def initialize_game():
    """게임을 초기 상태로 리셋합니다."""
    st.session_state.current_episode_id = "1"
    st.session_state.current_dialogue_id = "1"
    st.session_state.love_level = 0
    st.session_state.user_inputs = {}
    st.session_state.game_over = False
    st.session_state.user_name = "" # 사용자 이름 추가
    st.session_state.event_flags = set() # ✨ 어떤 이벤트를 겪었는지 저장할 '세트'

# --- 3. Streamlit 앱 메인 로직 ---
st.title("💖 두근두근 모쏠 탈출 프로젝트 💖")

# 한 번만 엑셀에서 로드 → 세션에 저장
if "episodes" not in st.session_state:
	episodes_db = load_episodes_from_excel(FILE_PATH)
	if episodes_db is None:
		st.error(f"`{FILE_PATH}` 파일을 찾을 수 없습니다!")
		st.stop()
	st.session_state.episodes = episodes_db

episodes = st.session_state.episodes  # 항상 세션에서 가져옴

if 'current_episode_id' not in st.session_state:
    initialize_game()

# --- 4. 사용자 이름 입력 (추가) ---
if st.session_state.user_name == "":
    st.subheader("게임을 시작하기 전에, 그녀가 부를 당신의 이름은?")
    name = st.text_input("이름을 입력하세요:")
    if st.button("이 이름으로 시작"):
        if name:
            st.session_state.user_name = name
            st.rerun()
        else:
            st.error("이름을 꼭 입력해주세요!")
    st.stop() # 이름 입력 전까지 게임 진행 중단

# --- 5. 게임 종료 화면 (동일) ---
elif st.session_state.game_over:
    st.header("게임 종료! 최종 호감도")
    st.metric(label="호감도 점수", value=st.session_state.love_level)
    
    # (엔딩 분기... 동일)
    if st.session_state.love_level >= 20:
        st.image(IMAGE_PATH + 'pepe_suc.png')
        st.success("### (1년 후.. ) \n ### 오늘은 000의 1주년이다. 얼른 이벤트 준비하러 가야지 ㅎ\n\n\n  축하합니다! 그녀와 이어졌습니다! 💖")
    elif st.session_state.love_level >= 7:
        st.image(IMAGE_PATH + 'pepe_friend.png')
        st.error("### (1년 후.. ) \n ### 오늘은 수지의 생일. 그땐 좋았는데,, 이젠 그저 친구로 남기로 했다. \n\n 수지는 당신과 친구로 남기로 했습니다")
    else:
        st.image(IMAGE_PATH + 'pepe_sad.png')
        st.error("### (1년 후) \n ###  헉헉.. 어째서 그날의 꿈을... 모솔의 나는 여전히 그날의 추억으로 하루를 살아간다. \n\n그녀와 이어지지 못했습니다 ... 💔")

    st.subheader("당신이 입력한 답변 모음")
    st.json(st.session_state.user_inputs)
    
    
    if st.button("처음부터 다시 시작하기"):
        st.session_state.episodes = load_episodes_from_excel(FILE_PATH)
        initialize_game()
        st.rerun()

# --- 6. 게임 진행 화면 ---
else:
    st.metric(label="현재 호감도", value=st.session_state.love_level)
    
    episode_num = st.session_state.current_episode_id
    dialogue_num = st.session_state.current_dialogue_id
    
    if episode_num not in st.session_state.episodes:
        st.session_state.game_over = True
        st.rerun()
    
    else:
        # 1. 엑셀에서 '기본' 대화 정보를 불러옵니다. (.copy()로 복사본 사용)
        dialogue = st.session_state.episodes[episode_num][dialogue_num].copy()

        # 3. 폼(Form) 렌더링 (수정된 dialogue 객체 사용)
        st.divider()

        # 이미지 띄우기 관련
        if episode_num == "1" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'pepe_game.png')
        elif episode_num == "1" and dialogue_num == "2":
            st.image(IMAGE_PATH + 'lz_happy.png')
        elif episode_num == "1" and dialogue_num == "3":
            st.image(IMAGE_PATH + 'lz_happy.png')
        elif episode_num == "1" and dialogue_num == "4":
            # 플래그 확인 코드
            if "LATTE" in st.session_state.event_flags:
                st.image(IMAGE_PATH + 'lz_latte.png')
            elif "MINT_CHOCO" in st.session_state.event_flags:
                st.image(IMAGE_PATH + 'lz_mint.png')
            else:
                st.image(IMAGE_PATH + 'lz_order.png')
        elif episode_num == "2" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'pepe_look.png')
        elif episode_num == "2" and dialogue_num == "2":
            st.image(IMAGE_PATH + 'pepe_look.png')
        elif episode_num == "4" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'pepe_41.png')
        elif episode_num == "4" and dialogue_num == "2":
            st.image(IMAGE_PATH + 'lz_talk.png')
        elif episode_num == "5" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'lz_climb.png')
        elif episode_num == "6" and dialogue_num == "1":
            if "ATTENDED_CLASS" in st.session_state.event_flags:
                st.image(IMAGE_PATH + 'lz_genious.png')
            elif "SKIPPED_CLASS" in st.session_state.event_flags:
                st.image(IMAGE_PATH + 'lz_genious.png')
            else:
                st.image(IMAGE_PATH + 'lz.climb.png')
        elif episode_num == "7" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'lz_band.png')
        elif episode_num == "7" and dialogue_num == "2":
            st.image(IMAGE_PATH + 'lz_climb.png')
        elif episode_num == "7" and dialogue_num == "3":
            st.image(IMAGE_PATH + 'lz_samulnori.png')
        elif episode_num == "8" and dialogue_num == "1":
            st.image(IMAGE_PATH + 'lz_firework.png')
        else:
            st.image(IMAGE_PATH + 'wallpaper.png')


        st.subheader(dialogue['text'].replace("00", st.session_state.user_name))
        st.sidebar.selectbox('상황',f'Episode {episode_num}-{dialogue_num}')
        with st.form(key=f"ep_{episode_num}_{dialogue_num}_form"):
            choices_list = list(dialogue["choices"].keys())
            user_choice = st.radio(
                label=dialogue["question"], # Q를 라디오 라벨로 사용
                options=choices_list,
                index=None
            )
            
            # # 4. [핵심] 분기점에 따른 '추가 질문' 처리 (선택)
            # # Ep3-1이면서, "도와준다"를 선택한 경우에만 추가 질문을 띄움
            # show_extra_question = False
            # if False: # episode_num == "3" and dialogue_num == "1" and user_choice == "도와준다.":
            #     show_extra_question = True
            # user_question_answer = st.text_input(label="정답을 적어주세요:")
            # else:
            # user_question_answer = "N/A" # 해당 없는 경우는 NA 처리

            submit_button = st.form_submit_button(label="선택 완료")



        # 5. 제출 버튼 로직
        if submit_button:
            # (질문이 필요한데 답변을 안 한 경우 예외처리)
            if not user_choice: # or not user_question_answer:
                st.error("모든 항목을 선택하고 답변을 입력해주세요!")
            
            else:
                love_change = 0
                
                # # 6.  [핵심] 분기점 '결과' 처리 (하드코딩)
                # # Ep3-1의 "도와준다"는 플래그에 따라 결과가 다름
                if episode_num == "5" and dialogue_num == "1" and user_choice == "도와준다":
                    if "ATTENDED_CLASS" in st.session_state.event_flags:
                        love_change = 10
                        jump_to_result = "『너 진짜 똑똑하다! 담에도 나랑 과제 해줄거지???』 \n"
                    elif "SKIPPED_CLASS" in st.session_state.event_flags:
                        love_change = 0
                        jump_to_result = " 큰일났습니다. 수업을 째서 아는게 없습니다! \n『뭐야 ㅋㅋ 너도 암것도 모르네! 바보』\n"
                    else: # (예외)
                        love_change = 0
                        jump_to_result = "고.. 고마워!"
                    
                elif episode_num == "8" and dialogue_num == "1":
                    if "SAMULLORI" in st.session_state.event_flags:
                        love_change = -200
                    jump_to_result = None
                # 그 외 모든 일반적인 선택지 처리 (엑셀 기본값 사용)
                else:
                    love_change = dialogue["choices"][user_choice][0]
                    jump_to_result = dialogue["choices"][user_choice][1]

                # # 7. [핵심] 플래그 저장
                # # Ep2-1의 선택에 따라 플래그를 '기록'
                if episode_num == "1" and dialogue_num == "3":
                    if user_choice == "크흠... 라떼 아이스로 휘핑은 두 번!! 시나몬 파우더 올려주고 얼음은 3개만 넣어주세요":
                        st.session_state.event_flags.add("LATTE")
                    elif user_choice == "민트초코프라페 주세요":
                        st.session_state.event_flags.add("MINT_CHOCO")
                    else:
                        st.session_state.event_flags.add("AMERICANO")

                if episode_num == "4" and dialogue_num == "1":
                    if user_choice == "째고 산책":
                        st.session_state.event_flags.add("SKIPPED_CLASS")
                    elif user_choice == "(그래도 학생은 공부해야지...)":
                        st.session_state.event_flags.add("ATTENDED_CLASS")
                elif episode_num == "6" and dialogue_num == "1":
                    if user_choice == "자네 사물놀이패 '삼다수통제조사'에 들어오지 않겠나? \\n 신입은 언제나 환영이라네":
                        st.session_state.event_flags.add("SAMULLORI")

                # if love_change > 0:
                #     feedback_toast = f"호감도가 {love_change}만큼 상승했습니다! 🥰"
                # elif love_change < 0:
                #     feedback_toast = f"호감도가 {love_change}만큼 하락했습니다... 🥶"
                # else:
                #     feedback_toast = "아무런 변화가 없습니다. 😐"

                # 8. 상태 업데이트
                st.session_state.love_level += love_change
                
                input_key = f"Ep {episode_num}-{dialogue_num}"
                st.session_state.user_inputs[f"{input_key} 선택"] = user_choice
                # if user_question_answer != "N/A": # 답변이 있었던 경우에만 저장
                #     st.session_state.user_inputs[f"{input_key} 답변"] = user_question_answer
                
                # st.toast(feedback_toast, icon="💖" if love_change > 0 else "💔")
                
                # 다음 대화로 이동

                if isinstance(jump_to_result, str):
                    if "*" in jump_to_result:
                        next_episode_num = jump_to_result.split("*")[0]
                        st.session_state.current_episode_id = next_episode_num
                        next_dialogue_num = jump_to_result.split("*")[1]
                        st.session_state.current_dialogue_id = next_dialogue_num
                    else:
                        next_dialogue_num = str(int(dialogue_num) + 1)
                        if next_dialogue_num not in st.session_state.episodes[episode_num]:
                            next_episode_num = str(int(episode_num) + 1)
                            next_dialogue_num = "1"
                            st.session_state.episodes[next_episode_num][next_dialogue_num]["text"] = jump_to_result.replace("\\n", "\n").replace("00", st.session_state.user_name) + st.session_state.episodes[next_episode_num][next_dialogue_num]["text"]
                            st.session_state.current_episode_id = next_episode_num
                        else:
                            st.session_state.episodes[st.session_state.current_episode_id][next_dialogue_num]["text"] = jump_to_result.replace("\\n", "\n").replace("00", st.session_state.user_name) + st.session_state.episodes[st.session_state.current_episode_id][next_dialogue_num]["text"]
                        st.session_state.current_dialogue_id = next_dialogue_num
                else:
                    next_dialogue_num = str(int(dialogue_num) + 1)
                    if next_dialogue_num not in st.session_state.episodes[episode_num]:
                        next_episode_num = str(int(episode_num) + 1)
                        next_dialogue_num = "1"
                        st.session_state.current_episode_id = next_episode_num
                    st.session_state.current_dialogue_id = next_dialogue_num
                
                
                st.rerun()