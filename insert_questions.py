#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
question.jsonの内容をPostgreSQLのquestionsテーブルに挿入するスクリプト
"""

import json
import psycopg2
import os
import logging
from typing import Dict, List, Any

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_questions_json(file_path: str) -> Dict[str, Any]:
    """
    question.jsonファイルを読み込む
    
    Args:
        file_path: JSONファイルのパス
        
    Returns:
        JSONデータの辞書
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSONファイルを正常に読み込みました: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSONファイルの解析に失敗しました: {e}")
        raise


def get_db_connection():
    """
    PostgreSQLデータベースへの接続を取得
    
    Returns:
        データベース接続オブジェクト
    """
    # 環境変数またはデフォルト値を使用
    db_config = {
        'host': 'it-passport-text2csv-db-1',
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        logger.info("データベースに正常に接続しました")
        return conn
    except psycopg2.Error as e:
        logger.error(f"データベース接続に失敗しました: {e}")
        raise


def map_json_to_db_row(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSONデータをデータベースの行にマッピング
    
    Args:
        question_data: 個々の問題データ
        
    Returns:
        データベースに挿入するための行データ
    """
    mapping = {
        "question_number": "id",
        "question_type": "type", 
        "question_text": "question",
        "options": "options",
        "question_answer": "answer"
    }
    
    db_row = {}
    
    for json_key, db_column in mapping.items():
        if json_key in question_data:
            value = question_data[json_key]
            
            # question_numberは数値として扱う
            if db_column == "id":
                try:
                    db_row[db_column] = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"question_numberを数値に変換できません: {value}")
                    db_row[db_column] = None
            # optionsは配列として扱う
            elif db_column == "options":
                if isinstance(value, list):
                    db_row[db_column] = value
                else:
                    logger.warning(f"optionsが配列ではありません: {value}")
                    db_row[db_column] = []
            else:
                db_row[db_column] = str(value) if value is not None else None
        else:
            logger.warning(f"必要なキー '{json_key}' が見つかりません")
            db_row[mapping[json_key]] = None
    
    return db_row


def insert_questions(conn, questions_data: List[Dict[str, Any]]) -> int:
    """
    questionsテーブルにデータを挿入
    
    Args:
        conn: データベース接続
        questions_data: 挿入する問題データのリスト
        
    Returns:
        挿入された行数
    """
    cursor = conn.cursor()
    
    # テーブルをクリア（既存データを削除）
    try:
        cursor.execute("TRUNCATE TABLE questions RESTART IDENTITY;")
        logger.info("既存のデータをクリアしました")
    except psycopg2.Error as e:
        logger.error(f"テーブルクリアに失敗しました: {e}")
        raise
    
    # INSERT文のSQL
    insert_sql = """
    INSERT INTO questions (id, question, type, options, answer)
    VALUES (%(id)s, %(question)s, %(type)s, %(options)s, %(answer)s)
    """
    
    inserted_count = 0
    
    for question_data in questions_data:
        try:
            db_row = map_json_to_db_row(question_data)
            
            # 必須フィールドのチェック
            if db_row.get('id') is None:
                logger.warning(f"IDが無効なためスキップします: {question_data}")
                continue
                
            cursor.execute(insert_sql, db_row)
            inserted_count += 1
            
            logger.debug(f"問題 {db_row['id']} を挿入しました")
            
        except psycopg2.Error as e:
            logger.error(f"データ挿入に失敗しました: {question_data} - エラー: {e}")
            # エラーが発生した場合はロールバック
            conn.rollback()
            raise
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            conn.rollback()
            raise
    
    # コミット
    conn.commit()
    cursor.close()
    
    logger.info(f"合計 {inserted_count} 件のデータを挿入しました")
    return inserted_count


def main():
    """
    メイン処理
    """
    # ファイルパス
    json_file_path = os.path.join(os.path.dirname(__file__), 'outputs', 'questions.json')
    
    try:
        # JSONファイルを読み込み
        data = load_questions_json(json_file_path)
        questions = data.get('questions', [])
        
        if not questions:
            logger.warning("問題データが見つかりません")
            return
        
        logger.info(f"読み込んだ問題数: {len(questions)}")
        
        # データベースに接続
        with get_db_connection() as conn:
            # データを挿入
            inserted_count = insert_questions(conn, questions)
            
            logger.info(f"処理完了: {inserted_count} 件のデータを挿入しました")
            
    except Exception as e:
        logger.error(f"処理に失敗しました: {e}")
        raise


if __name__ == "__main__":
    main()
