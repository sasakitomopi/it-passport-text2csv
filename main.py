import re

text = """
問1 A社がB社に作業の一部を請負契約で委託している。 作業形態 a 〜 c のうち, いわ
ゆる偽装請負とみなされる状態だけを全て挙げたものはどれか。

a B社の従業員が, A 社内において, A社の責任者の指揮命令の下で, 請負契約で
取り決めた作業を行っている。
b B社の従業員が, A 社内において, B社の責任者の指揮命令の下で, 請負契約で
取り決めた作業を行っている。
c B社の従業員が, B 社内において, A社の責任者の指揮命令の下で, 請負契約で
取り決めた作業を行っている。
ア a       イ a,b     ウ a, c      エ b,c

問2 従来の情報セキュリティマネジメントシステム規格を基礎に追加で制定されたも
ので, クラウドサービスに対応した情報セキュリティ管理体制を構築するためのガ
イドライン規格として, 最も適切なものはどれか。
ア IS0 14001               イ JIS Q 15001
ウ TIS0/IEC 27017            エ IS0 9001
"""

# 全体のテキストを改行で分割して、各行を処理しやすくする
lines = text.strip().split('\n')

# 問題と選択肢を格納するリスト
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
        options.extend(re.split(r'\s{2,}', line.strip()))
        continue

    # 問題文の続きを追記（複数行にわたる場合）
    if 'question_text' in current_question and line and not answer_option_pattern.match(line) and not re.match(r'^[a-z]\s', line):
        current_question['question_text'] += ' ' + line.strip()
    
    # 選択肢 (a, b, c) を追加
    if re.match(r'^[a-z]\s', line):
        options.append(line.strip())


# 最後の問題を保存
if current_question:
    current_question['options'] = options
    parsed_data.append(current_question)

# 結果の表示
for q in parsed_data:
    print(f"--- 問{q['question_number']} ---")
    print("問題文:", q['question_text'])
    print("選択肢:")
    for opt in q['options']:
        print(f"  - {opt}")
    print("\n")