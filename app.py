from flask import Flask, request, render_template, jsonify
import openai
import os
from dotenv import load_dotenv
import re
import requests
from bs4 import BeautifulSoup

# .envファイルを読み込む
load_dotenv()

app = Flask(__name__)
app.secret_key = 'greenhill'

# 環境変数からAPIキーを取得
api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI(api_key=api_key)

def scrape_and_summarize(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        text = re.sub(r'\s+', ' ', text)
        summary_prompt = f"""
        あなたはWebサイト分析の専門家です。
        以下はある企業サイトの文章です。競合としてどのような特徴・強みを打ち出しているか簡潔にまとめてください。

        {text[:3000]}

        【出力形式】
        - 主な特徴：...
        - 訴求しているポイント：...
        """
        summary_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return summary_response.choices[0].message.content.strip()
    except Exception as e:
        return f"（競合サイトの取得・要約に失敗しました: {e}）"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json

    # 入力取得
    purpose = data.get("purpose", [])
    target_type = data.get("target_type", "")
    age = data.get("age", "")
    gender = data.get("gender", "")
    job = data.get("job", "")
    interest = data.get("interest", "")
    industry = data.get("industry", "")
    product = data.get("product", "")
    region = data.get("region", "")
    strength = data.get("strength", "")
    competitor_urls = data.get("competitor", [])
    competitor_summaries = [scrape_and_summarize(url) for url in competitor_urls if url]
    competitor_summary = "\n\n".join(competitor_summaries) if competitor_summaries else "（競合情報なし）"

    # 初回プロンプト
    initial_prompt = f"""
    あなたはLP構成の専門家です。
    以下の情報を元に、効果的な訴求ポイントを1つだけ抽出し、その訴求に沿ったLP構成案をHTML形式で提案してください。

    【背景・目的】
    - LPの目的：{', '.join(purpose)}
    - ターゲット：{target_type}

    【ペルソナ】
    - 年齢：{age}
    - 性別：{gender}
    - 職業：{job}
    - 興味関心：{interest}

    【サービス情報】
    - 業種：{industry}
    - サービス・商品：{product}
    - 地域：{region}
    - 強み・特徴：{strength}
    - 競合サイトの要約：{competitor_summary}

    【出力形式】
    <h3>競合との比較分析</h3>
    <p>...内容...</p>

    <h3>効果的な訴求ポイント</h3>
    <p>...内容...</p>

    なお、以下に示すのは一般的なセクション構成の一例です。
    実際の構成では、フォームで入力された目的・商品・ターゲット情報に応じて、必要なものを選び、不必要なものは省略し、新たに必要と思われるセクションがあれば追加してください。

    【一般的なLP構成の一例】
    - Kv（キービジュアル）
    - Issue（抱える課題）
    - Solution（提供する解決策）
    - Service（製品・サービスの強み）
    - Works（実績）
    - Voice（お客様の声）
    - FAQ（よくある質問）
    - CTA（資料請求・問い合わせ）
    - Footer（会社情報など）

    各セクションは以下のHTML構造で記述してください：
    <div class='mb-4'>
      <h4>セクション名</h4>
      <strong>見出し：</strong> ...<br>
      <strong>含めるべきコンテンツ：</strong> ...<br>
    </div>
    """

    print("\n===== 初回プロンプト =====\n")
    print(initial_prompt)
    print("\n===========================\n")

    initial_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": initial_prompt}]
    )
    initial_output = initial_response.choices[0].message.content.strip()

    # 初回出力の抽出
    comparison_match = re.search(r"<h3>競合との比較分析</h3>\s*<p>(.*?)</p>", initial_output, re.DOTALL)
    appeal_match = re.search(r"<h3>効果的な訴求ポイント</h3>\s*<p>(.*?)</p>", initial_output, re.DOTALL)
    structure_match = re.search(r"<div class='mb-4'>.*?</div>(?:\s*<div class='mb-4'>.*?</div>)*", initial_output, re.DOTALL)

    comparison_section = comparison_match.group(1).strip() if comparison_match else "(比較分析の取得に失敗しました)"
    appeal_section_initial = appeal_match.group(1).strip() if appeal_match else "(訴求ポイントの取得に失敗しました)"
    structure_section_initial = structure_match.group(0).strip() if structure_match else "(LP構成案の取得に失敗しました)"

    # 改善プロンプト（訴求と構成案のみ）
    revise_prompt = f"""
    以下は初回に出力されたLP構成案です。
    この中から「訴求ポイント」と「構成案」のクオリティをさらに高めてください。
    比較分析部分はそのままで構いません。

    【初回構成案】
    <h3>効果的な訴求ポイント</h3>
    <p>{appeal_section_initial}</p>

    {structure_section_initial}

    【出力形式】
    <h3>効果的な訴求ポイント</h3>
    <p>...</p>

    <h3>LP構成案</h3>
    <div class='mb-4'>...</div>
    """

    print("\n===== 改善プロンプト =====\n")
    print(revise_prompt)
    print("\n===========================\n")

    revise_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": revise_prompt}]
    )
    revise_output = revise_response.choices[0].message.content.strip()

    appeal_match_final = re.search(r"<h3>効果的な訴求ポイント</h3>\s*<p>(.*?)</p>", revise_output, re.DOTALL)
    structure_match_final = re.search(r"<div class='mb-4'>.*?</div>(?:\s*<div class='mb-4'>.*?</div>)*", revise_output, re.DOTALL)

    appeal_section_final = appeal_match_final.group(1).strip() if appeal_match_final else "(改善された訴求ポイントの取得に失敗しました)"
    structure_section_final = structure_match_final.group(0).strip() if structure_match_final else "(改善された構成案の取得に失敗しました)"

    return jsonify({
        "comparison": f"<p>{comparison_section}</p>",
        "appeal_point": f"<p>{appeal_section_final}</p>",
        "lp_structure": structure_section_final
    })

if __name__ == "__main__":
    app.run(debug=True)
