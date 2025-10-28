# app.py
import streamlit as st
from db_manager import DBManager
from db_backup import DBExecute
import time
import pandas as pd
import os
import sqlite3
import re

# --- Configurações Iniciais ---
st.set_page_config(layout="wide", page_title="Concurseiro Pro")
DB_FILE, CSV_FILE, USER_ID = "concurso.db", "questoes.csv", "Concurseiro"
@st.cache_resource
def get_db_manager(): return DBManager(DB_FILE)
db = get_db_manager()

def initialize_app():
    if 'app_initialized' not in st.session_state:
        if os.path.exists(CSV_FILE):
            count_before = db.get_summary(USER_ID)['total_questions']
            _, message = db.insert_questions_from_csv(CSV_FILE)
            st.cache_resource.clear()
            updated_db = get_db_manager()
            count_after = updated_db.get_summary(USER_ID)['total_questions']
            if count_after > count_before: st.toast(message, icon="✔️")
            else: st.toast("Banco de dados já atualizado.", icon="ℹ️")
        st.session_state.app_initialized = True

def initialize_session_state():
    if "current_page" not in st.session_state: st.session_state.current_page = "home"
    if "quiz_questions" not in st.session_state: st.session_state.quiz_questions = []
    if "current_question_index" not in st.session_state: st.session_state.current_question_index = 0
    if "start_time" not in st.session_state: st.session_state.start_time = None
    if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
    if "show_answer" not in st.session_state: st.session_state.show_answer = False

def reset_quiz_state():
    st.session_state.quiz_started = False; st.session_state.current_page = "home"

def start_quiz(disciplines=None, topics=None, mode=None, review_mode=False, weakest_topics=None):
    if review_mode and weakest_topics:
        disciplines = list(set([rec['discipline'] for rec in weakest_topics])); topics = [rec['topic'] for rec in weakest_topics]; mode = "wrong"
    st.session_state.quiz_questions = db.get_questions(discipline_filter=disciplines, topic_filter=topics, selection_mode=mode, user_id=USER_ID)
    if not st.session_state.quiz_questions: st.warning("Nenhuma questão encontrada com os filtros.")
    else:
        st.session_state.current_page = "quiz"; st.session_state.quiz_started = True; st.session_state.current_question_index = 0
        st.session_state.show_answer = False; st.session_state.start_time = time.time(); st.rerun()

def home_page():
    st.title("📚 Concurseiro Pro: Início")
    if not os.path.exists(CSV_FILE): st.error(f"'{CSV_FILE}' não encontrado!", icon="🚨"); st.warning(f"Crie um arquivo `{CSV_FILE}` com 11 colunas."); return
    
    summary = db.get_summary(USER_ID)
    if summary['total_questions'] == 0: st.info("Nenhuma questão no banco de dados."); return
    
    st.subheader("Resumo Geral")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", summary["total_questions"]); col2.metric("Respondidas", summary["answered_questions"]); col3.metric("Acertos", summary["correct_answers"]); col4.metric("Erros", summary["wrong_answers"])
    
    st.divider()
    st.subheader("🧠 Sugestão de Estudo")
    weakest_topics = db.get_weakest_topics(USER_ID, top_n=5)
    if weakest_topics:
        st.warning("Assuntos a melhorar (com base nos erros):")
        for rec in weakest_topics:
            st.markdown(f"- **{rec['topic']}** ({rec['discipline']})")
        if st.button("Revisar esses assuntos", type="primary"): 
            start_quiz(review_mode=True, weakest_topics=weakest_topics)
    else: 
        st.info("Responda mais questões para receber sugestões.")
    
    st.divider()
    with st.form("filter_form"):
        st.subheader("Iniciar Nova Sessão")
        disciplines = st.multiselect("Disciplinas", options=db.get_all_disciplines()); topics = st.multiselect("Assuntos", options=db.get_all_topics())
        mode = st.radio("Modo:", options=["random", "unanswered", "wrong", "correct"], format_func=lambda x: {"random": "Aleatório", "unanswered": "Nunca respondi", "wrong": "Que já errei", "correct": "Que já acertei"}[x], horizontal=True)
        if st.form_submit_button("Começar Sessão", use_container_width=True): 
            start_quiz(disciplines=disciplines, topics=topics, mode=mode)

    # --- NOVA SEÇÃO DE BACKUP E RESTAURAÇÃO ---
    st.divider()
    with st.expander("⚙️ Backup e Restauração de Dados"):
        st.subheader("Backup (Exportar)")
        st.info("Clique no botão abaixo para baixar o arquivo do banco de dados (`concurso.db`), que contém todas as suas questões e seu histórico de respostas.")
        
        try:
            with open(DB_FILE, "rb") as fp:
                st.download_button(
                    label="Baixar Backup do Banco de Dados",
                    data=fp,
                    file_name="concurso_backup.db",
                    mime="application/octet-stream"
                )
        except FileNotFoundError:
            st.warning("O banco de dados ainda não foi criado. Responda pelo menos uma questão primeiro.")

        st.subheader("Restauração (Importar)")
        st.warning("🚨 **Atenção:** Fazer o upload de um backup irá **substituir permanentemente** todos os seus dados atuais (questões e histórico). Faça isso apenas se tiver certeza.")
        
        uploaded_db = st.file_uploader(
            "Selecione um arquivo de backup (.db) para restaurar",
            type="db"
        )
        
        if uploaded_db is not None:
            # Pega os bytes do arquivo enviado
            backup_bytes = uploaded_db.getvalue()
            
            # Escreve os bytes por cima do arquivo de banco de dados atual
            with open(DB_FILE, "wb") as f:
                f.write(backup_bytes)
            
            # Limpa todos os caches e reinicia o app para carregar o novo DB
            st.cache_resource.clear()
            st.success("Backup restaurado com sucesso! A página será recarregada com os novos dados.")
            time.sleep(2) # Pausa para o usuário ler a mensagem
            st.rerun()

def statistics_page():
    # ... (sem mudanças)
    st.title("📊 Estatísticas"); stats_df = db.get_detailed_statistics(USER_ID)
    if stats_df.empty: 
        st.info("Responda questões para ver suas estatísticas aqui."); 
        DBExecute()
        return
    st.subheader("Desempenho por Disciplina"); discipline_summary = stats_df.groupby('discipline').agg(total_answered=('total_answered', 'sum'), total_correct=('total_correct', 'sum')).reset_index()
    discipline_summary['accuracy_percentage'] = (discipline_summary['total_correct'] / discipline_summary['total_answered']) * 100
    for _, row in discipline_summary.iterrows():
        st.markdown(f"#### {row['discipline']}"); col1, col2, col3 = st.columns([3, 1, 1]); col1.progress(int(row['accuracy_percentage'])); col2.metric("Acerto", f"{row['accuracy_percentage']:.1f}%"); col3.metric("Respondidas", f"{int(row['total_correct'])}/{int(row['total_answered'])}")
        with st.expander(f"Ver detalhes de {row['discipline']}"):
            topic_df = stats_df[stats_df['discipline'] == row['discipline']].sort_values(by='accuracy_percentage')
            st.dataframe(topic_df[['topic', 'accuracy_percentage', 'total_correct', 'total_answered']], hide_index=True, use_container_width=True, column_config={"topic": "Assunto", "accuracy_percentage": st.column_config.ProgressColumn("Acerto (%)", format="%.1f%%", min_value=0, max_value=100), "total_correct": "Acertos", "total_answered": "Total"})

def quiz_page():
    # ... (sem mudanças)
    if not st.session_state.get('quiz_questions'): st.warning("Sessão não iniciada."); st.button("Voltar ao Início", on_click=reset_quiz_state); return
    idx = st.session_state.current_question_index
    if idx >= len(st.session_state.quiz_questions): st.success("🎉 Sessão finalizada."); st.button("Voltar ao Início", type="primary", on_click=reset_quiz_state); return
    q = st.session_state.quiz_questions[idx]
    st.title(f"Questão {idx + 1}/{len(st.session_state.quiz_questions)}"); st.caption(f"Disciplina: {q.get('discipline', 'N/A')} | Assunto: {q.get('topic', 'N/A')}"); st.subheader(q.get('title', '')); st.write(f"**{q.get('text', 'Erro: Texto não encontrado.')}**")
    options_keys, options_labels = [], {}; alt_map = {'alt1': 'A', 'alt2': 'B', 'alt3': 'C', 'alt4': 'D', 'alt5': 'E'}
    for key, letter in alt_map.items():
        value = q.get(key)
        if value and str(value).strip(): cleaned_value = re.sub(r'^\s*(\([A-Ea-e]\)|[A-Ea-e][\.\)])\s*', '', value).strip(); options_keys.append(key); options_labels[key] = f"**{letter})** {cleaned_value}"
    if not options_keys: st.error("Erro: Nenhuma alternativa encontrada."); return
    st.radio("Escolha a alternativa:", options=options_keys, format_func=lambda k: options_labels.get(k), index=None, key=f"q_{q['id']}")
    if not st.session_state.show_answer:
        col1, col2, col3 = st.columns(3); is_first_question = (idx == 0)
        with col1:
            if st.button("⬅️ Voltar", use_container_width=True, disabled=is_first_question): st.session_state.current_question_index -= 1; st.session_state.start_time = time.time(); st.rerun()
        with col2:
            if st.button("Responder 📝", use_container_width=True, type="primary"):
                selected_key = st.session_state[f"q_{q['id']}"]
                if selected_key is None: st.warning("Selecione uma alternativa.")
                else: is_correct = (alt_map[selected_key] == q['answer']); db.record_history(q['id'], USER_ID, int((time.time() - st.session_state.start_time) * 1000), is_correct, alt_map[selected_key]); st.session_state.show_answer = True; st.session_state.last_selection = alt_map[selected_key]; st.rerun()
        with col3:
            if st.button("Pular ➡️", use_container_width=True): st.session_state.current_question_index += 1; st.session_state.start_time = time.time(); st.rerun()
    else:
        st.divider()
        if st.session_state.last_selection == q['answer']: st.success(f"✅ Correto! ({q['answer']})")
        else: st.error(f"❌ Incorreto. A resposta é **{q['answer']}** (você marcou {st.session_state.last_selection}).")
        st.info(f"**Explicação:** {q.get('explanation', '')}")
        with st.expander("Ver histórico da questão"):
            history = db.get_question_history(q['id'], USER_ID)
            if history: df_h = pd.DataFrame(history); df_h['is_correct'] = df_h['is_correct'].apply(lambda x: "✔️" if x else "❌"); st.dataframe(df_h[['answered_at', 'is_correct', 'selected_alternative']], hide_index=True)
            else: st.write("Primeira vez respondendo.")
        if st.button("Próxima Questão ➡️", use_container_width=True, type="primary"): st.session_state.current_question_index += 1; st.session_state.show_answer = False; st.session_state.start_time = time.time(); st.rerun()

if __name__ == "__main__":
    initialize_app()
    initialize_session_state()
    with st.sidebar:
        st.title("Menu"); st.button("Início", use_container_width=True, type="primary" if st.session_state.current_page == "home" else "secondary", on_click=lambda: st.session_state.update(current_page="home"))
        st.button("Estatísticas", use_container_width=True, type="primary" if st.session_state.current_page == "statistics" else "secondary", on_click=lambda: st.session_state.update(current_page="statistics"))
        st.divider()
        if st.session_state.quiz_started:
            st.info(f"Quiz em andamento...\nQuestão {st.session_state.current_question_index + 1}/{len(st.session_state.quiz_questions)}")
            if st.session_state.current_page != 'quiz': st.button("Voltar para o Quiz", use_container_width=True, on_click=lambda: st.session_state.update(current_page="quiz"))
            st.button("Sair do Quiz", use_container_width=True, on_click=reset_quiz_state)
    if st.session_state.current_page == "home": home_page()
    elif st.session_state.current_page == "statistics": statistics_page()
    elif st.session_state.current_page == "quiz": quiz_page()
