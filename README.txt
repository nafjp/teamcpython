Python 版 Azure Functions (v2 programming model) の最小構成です。

使い方:
1. Python 3.11 系を入れる
2. このフォルダで仮想環境を作る
3. pip install -r requirements.txt
4. local.settings.example.json を local.settings.json にコピーして値を入れる
5. func start
6. 問題なければ func azure functionapp publish <FunctionAppName>

主要ファイル:
- function_app.py: HTTP エンドポイント /api/analyze-meal
- src/openai_client.py: Azure OpenAI 呼び出し
- src/cosmos_client.py: Cosmos DB 保存
- src/date_utils.py: meal_date 補助
- src/prompts.py: 会話用と抽出用のプロンプト
