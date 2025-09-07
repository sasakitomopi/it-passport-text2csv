#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Any

def extract_questions_from_text(text_content: str) -> List[Dict[str, Any]]:
    """
    テキストから問題番号・問題文・選択肢を抽出する
    main.pyのロジックを参考に実装
    """
    lines = text_content.strip().split('\n')
    parsed_data = []
    current_question = {}
    options = []
    
    # 問題の開始を検知するための正規表現
    question_start_pattern = re.compile(r'^問(\d+)\s(.*)')
    # 選択肢の開始を検知するための正規表現 (ア、イ、ウ、エ)
    answer_option_pattern = re.compile(r'^[アイウエ]\s')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 問題文の開始をチェック
        match = question_start_pattern.match(line)
        if match:
            if current_question:
                # 前の問題を保存
                current_question['options'] = options
                parsed_data.append(current_question)
                options = []
            
            # 新しい問題の情報を初期化
            current_question = {
                'question_number': match.group(1),
                'question_text': match.group(2).strip()
            }
            continue
        
        # 選択肢の開始をチェック (「ア」〜「エ」で始まる行)
        if answer_option_pattern.match(line):
            # 2つ以上のスペースで分割
            options.extend(re.split(r'\s{2,}', line.strip()))
            continue
        
        # 問題文の続きを追記（複数行にわたる場合）
        if 'question_text' in current_question and line and not answer_option_pattern.match(line):
            current_question['question_text'] += '\n' + line.strip()
    
    # 最後の問題を保存
    if current_question:
        current_question['options'] = options
        parsed_data.append(current_question)
    
    return parsed_data

def determine_question_type(file_path: str) -> str:
    """
    ファイルパスから問題の種類を判定する
    """
    if 'management' in file_path:
        return 'management'
    elif 'strategy' in file_path:
        return 'strategy'
    elif 'technology' in file_path:
        return 'technology'
    else:
        return 'unknown'

def process_all_text_files(base_directory: str) -> List[Dict[str, Any]]:
    """
    指定されたディレクトリ配下の全テキストファイルを処理する
    """
    all_questions = []
    base_path = Path(base_directory)
    
    # .txtファイルを再帰的に検索
    for txt_file in base_path.rglob('*.txt'):
        print(f"処理中: {txt_file}")
        
        try:
            # ファイルの内容を読み込む
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 問題の種類を判定
            question_type = determine_question_type(str(txt_file))
            
            # テキストから問題を抽出
            questions = extract_questions_from_text(content)
            
            # 各問題に問題の種類を追加
            for question in questions:
                question['question_type'] = question_type
                all_questions.append(question)
        
        except Exception as e:
            print(f"エラー: {txt_file} の処理中にエラーが発生しました: {e}")
            continue
    
    return all_questions

def load_answers(answer_file: str) -> Dict[str, str]:
    """
    answer.jsonファイルから解答情報を読み込み、問題番号をキーとした辞書を作成する
    """
    answers_dict = {}
    
    try:
        with open(answer_file, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        for answer_item in answers_data:
            question_number = answer_item.get('question_number', '')
            question_answer = answer_item.get('question_answer', '')
            if question_number:
                answers_dict[question_number] = question_answer
                
        print(f"解答ファイル {answer_file} から {len(answers_dict)} 問の解答を読み込みました")
        
    except FileNotFoundError:
        print(f"警告: {answer_file} が見つかりません。解答情報なしで処理を続行します。")
    except Exception as e:
        print(f"エラー: {answer_file} の読み込み中にエラーが発生しました: {e}")
    
    return answers_dict

def save_to_json(questions: List[Dict[str, Any]], output_file: str, answers_dict: Dict[str, str] = None):
    """
    問題データをJSON形式で保存する（解答情報付き）
    """
    if answers_dict is None:
        answers_dict = {}
    
    # 指定された形式に変換
    json_data = {
        "questions": []
    }
    
    for question in questions:
        question_number = question.get('question_number', '')
        formatted_question = {
            "question_number": question_number,
            "question_type": question.get('question_type', 'unknown'),
            "question_text": question.get('question_text', ''),
            "options": question.get('options', []),
            "question_answer": answers_dict.get(question_number, '')
        }
        json_data["questions"].append(formatted_question)
    
    # JSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"結果を {output_file} に保存しました")
    print(f"総問題数: {len(questions)}")
    
    # 解答がマッピングされた問題数を表示
    answered_count = sum(1 for q in questions if answers_dict.get(q.get('question_number', ''), ''))
    print(f"解答付き問題数: {answered_count}")

def main():
    """
    メイン処理
    """
    # テキストファイルのディレクトリ
    texts_directory = "texts"
    
    # 解答ファイル
    answer_file = os.path.join("texts", "answer.json")
    
    # 出力ディレクトリとJSONファイル
    output_directory = "outputs"
    output_json = os.path.join(output_directory, "questions.json")
    
    print("IT passport テキストファイルのバッチ処理を開始します...")
    
    # ディレクトリの存在確認
    if not os.path.exists(texts_directory):
        print(f"エラー: {texts_directory} ディレクトリが見つかりません")
        return
    
    # 出力ディレクトリの作成
    os.makedirs(output_directory, exist_ok=True)
    print(f"出力ディレクトリ: {output_directory}")
    
    # 解答ファイルを読み込み
    print("\n解答情報を読み込んでいます...")
    answers_dict = load_answers(answer_file)
    
    # 全テキストファイルを処理
    print("\nテキストファイルを処理しています...")
    all_questions = process_all_text_files(texts_directory)
    
    if not all_questions:
        print("問題が見つかりませんでした")
        return
    
    # 問題番号でソート
    all_questions.sort(key=lambda x: int(x.get('question_number', '0')))
    
    # JSONファイルに保存（解答情報付き）
    print("\nJSONファイルを生成しています...")
    save_to_json(all_questions, output_json, answers_dict)
    
    # 統計情報の表示
    print("\n=== 処理結果統計 ===")
    type_counts = {}
    for question in all_questions:
        q_type = question.get('question_type', 'unknown')
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    for q_type, count in type_counts.items():
        print(f"{q_type}: {count}問")

if __name__ == "__main__":
    main()
