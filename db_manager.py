# db_manager.py (Versão Corrigida)
import sqlite3
import pandas as pd
from datetime import datetime

class DBManager:
    # ... (todo o início da classe: __init__, _initialize_db, insert_questions_from_csv, etc. permanece o mesmo) ...
    def __init__(self, db_path="concurso.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, text TEXT NOT NULL, alt1 TEXT, alt2 TEXT, alt3 TEXT, alt4 TEXT, alt5 TEXT, answer TEXT NOT NULL, explanation TEXT, discipline TEXT, topic TEXT, UNIQUE(text));")
        cursor.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER NOT NULL, user_id TEXT NOT NULL, response_time_ms INTEGER NOT NULL, answered_at TEXT NOT NULL, is_correct BOOLEAN NOT NULL, selected_alternative TEXT NOT NULL, FOREIGN KEY (question_id) REFERENCES questions (id));")
        conn.commit()
        conn.close()

    def insert_questions_from_csv(self, file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8', header=None)
            if df.shape[1] != 11: return False, f"Erro: CSV deve ter 11 colunas, mas tem {df.shape[1]}."
            df.columns = ['title', 'text', 'alt1', 'alt2', 'alt3', 'alt4', 'alt5', 'answer', 'explanation', 'discipline', 'topic']
            conn = sqlite3.connect(self.db_path)
            inserted, skipped = 0, 0
            for _, row in df.iterrows():
                try:
                    safe_row = tuple(v if pd.notna(v) else '' for v in row)
                    conn.execute("INSERT INTO questions (title, text, alt1, alt2, alt3, alt4, alt5, answer, explanation, discipline, topic) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", safe_row)
                    inserted += 1
                except sqlite3.IntegrityError: skipped += 1
            conn.commit()
            conn.close()
            return True, f"{inserted} novas inseridas. {skipped} duplicadas ignoradas."
        except Exception as e: return False, f"Erro ao processar CSV: {e}"

    def get_all_disciplines(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT discipline FROM questions WHERE discipline IS NOT NULL AND discipline != '' ORDER BY discipline;")
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_topics(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT topic FROM questions WHERE topic IS NOT NULL AND topic != '' ORDER BY topic;")
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    def get_questions(self, discipline_filter=None, topic_filter=None, selection_mode="random", user_id="Concurseiro"):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT q.* FROM questions q"
        join_clause, where_clauses, params = "", [], []
        if selection_mode != "random":
            join_clause = " LEFT JOIN (SELECT question_id, is_correct FROM history WHERE (question_id, answered_at) IN (SELECT question_id, MAX(answered_at) FROM history WHERE user_id = ? GROUP BY question_id)) h ON q.id = h.question_id"
            params.append(user_id)
            if selection_mode == "unanswered": where_clauses.append("h.question_id IS NULL")
            elif selection_mode == "wrong": where_clauses.append("h.is_correct = 0")
            elif selection_mode == "correct": where_clauses.append("h.is_correct = 1")
        if discipline_filter:
            where_clauses.append(f"q.discipline IN ({','.join('?' for _ in discipline_filter)})"); params.extend(discipline_filter)
        if topic_filter:
            where_clauses.append(f"q.topic IN ({','.join('?' for _ in topic_filter)})"); params.extend(topic_filter)
        if where_clauses: query += join_clause + " WHERE " + " AND ".join(where_clauses)
        else: query += join_clause
        query += " ORDER BY RANDOM()"
        cursor.execute(query, tuple(params))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
        
    # --- MUDANÇA APENAS AQUI ---
    def record_history(self, question_id, user_id, response_time_ms, is_correct, selected_alternative):
        conn = sqlite3.connect(self.db_path)
        answered_at = datetime.now().isoformat()
        # CORREÇÃO: A variável 'answered_at' foi adicionada à tupla de valores.
        conn.execute(
            "INSERT INTO history (question_id, user_id, response_time_ms, answered_at, is_correct, selected_alternative) VALUES (?, ?, ?, ?, ?, ?);",
            (question_id, user_id, response_time_ms, answered_at, is_correct, selected_alternative)
        )
        conn.commit()
        conn.close()

    def get_question_history(self, question_id, user_id="Concurseiro"):
        conn = sqlite3.connect(self.db_path); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute("SELECT * FROM history WHERE question_id = ? AND user_id = ? ORDER BY answered_at DESC;", (question_id, user_id))
        results = [dict(row) for row in cursor.fetchall()]; conn.close(); return results

    def get_summary(self, user_id="Concurseiro"):
        conn = sqlite3.connect(self.db_path)
        try: total_questions = pd.read_sql_query("SELECT COUNT(*) as count FROM questions;", conn).iloc[0, 0]
        except pd.io.sql.DatabaseError: return {"total_questions": 0, "answered_questions": 0, "unanswered_questions": 0, "correct_answers": 0, "wrong_answers": 0, "questions_by_discipline": {}}
        if total_questions == 0: conn.close(); return {"total_questions": 0, "answered_questions": 0, "unanswered_questions": 0, "correct_answers": 0, "wrong_answers": 0, "questions_by_discipline": {}}
        last_answers = pd.read_sql_query("SELECT h.is_correct FROM history h INNER JOIN (SELECT question_id, MAX(answered_at) AS max_date FROM history WHERE user_id = ? GROUP BY question_id) latest ON h.question_id = latest.question_id AND h.answered_at = latest.max_date", conn, params=(user_id,))
        correct = int(last_answers['is_correct'].sum()); answered = len(last_answers); wrong = answered - correct; unanswered = total_questions - answered
        q_by_disc = pd.read_sql_query("SELECT discipline, COUNT(*) as count FROM questions GROUP BY discipline ORDER BY discipline;", conn); conn.close()
        return {"total_questions": int(total_questions), "answered_questions": answered, "unanswered_questions": unanswered, "correct_answers": correct, "wrong_answers": wrong, "questions_by_discipline": pd.Series(q_by_disc['count'].values, index=q_by_disc['discipline']).to_dict()}

    def get_detailed_statistics(self, user_id="Concurseiro"):
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT q.discipline, q.topic, COUNT(h.id) AS total_answered, SUM(h.is_correct) AS total_correct FROM history h JOIN questions q ON h.question_id = q.id WHERE h.user_id = ? GROUP BY q.discipline, q.topic ORDER BY q.discipline, q.topic;", conn, params=(user_id,))
            if not df.empty: df['accuracy_percentage'] = (df['total_correct'] / df['total_answered']) * 100
            return df
        finally: conn.close()

    def get_weakest_topics(self, user_id="Concurseiro", top_n=5):
        stats_df = self.get_detailed_statistics(user_id)
        if stats_df.empty: return []
        relevant = stats_df[stats_df['total_answered'] >= 3].copy()
        if relevant.empty: relevant = stats_df.copy()
        weakest = relevant.sort_values(by='accuracy_percentage', ascending=True)
        return weakest.head(top_n)[['topic', 'discipline']].to_dict('records')