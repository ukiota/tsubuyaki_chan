import os
import json
import random
import discord
from janome.tokenizer import Tokenizer
import asyncio
import subprocess

# --- 設定 (GitHubのSecretsから読み込む) ---
TOKEN = os.environ.get("DISCORD_TOKEN")
LEARNING_CHANNEL_ID = int(os.environ.get("LEARNING_CHANNEL_ID", 0))
POSTING_CHANNEL_ID = int(os.environ.get("POSTING_CHANNEL_ID", 0))
MODEL_PATH = "markov_model.json"


# --- 関数定義 ---
def load_model():
    """ファイルからモデルを読み込む"""
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"__START__": []}

def save_model(data):
    """モデルをファイルに保存する"""
    with open(MODEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_sentence(data):
    """モデルから文章を生成する"""
    if not data.get("__START__"):
        return None
    
    sentence = []
    current_word = random.choice(data["__START__"])
    sentence.append(current_word)
    for _ in range(100):
        if current_word not in data: break
        next_word = random.choice(data[current_word])
        if next_word == "__END__": break
        sentence.append(next_word)
        current_word = next_word
    return "".join(sentence)

def commit_and_push_model():
    """変更されたモデルファイルをGitHubにコミット＆プッシュする"""
    try:
        # git statusで変更があるか確認
        subprocess.run(['git', 'diff-index', '--quiet', 'HEAD'], check=True)
        print("モデルファイルに変更はありませんでした。")
    except subprocess.CalledProcessError:
        print("モデルファイルに変更があったため、リポジトリに保存します。")
        subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'], check=True)
        subprocess.run(['git', 'add', MODEL_PATH], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update markov model'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print("リポジトリへの保存が完了しました。")

async def main_task():
    """Botのメイン処理（ログイン〜ログアウト）"""
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    markov_dict = load_model()

    @client.event
    async def on_ready():
        print(f'Bot: {client.user} として一時的にログインしました')
        
        learning_channel = client.get_channel(LEARNING_CHANNEL_ID)
        posting_channel = client.get_channel(POSTING_CHANNEL_ID)

        if not (learning_channel and posting_channel):
            print("エラー: 指定されたチャンネルIDが見つかりません。")
            await client.close()
            return
        
        # 1. 学習
        print(f"「{learning_channel.name}」で学習を開始します。")
        async for msg in learning_channel.history(limit=500):
            if msg.author.bot or msg.content.startswith(('!', '@')): continue
            words = list(t.tokenize(msg.content, wakati=True))
            if not words: continue
            if words[0] not in markov_dict["__START__"]:
                markov_dict["__START__"].append(words[0])
            for i in range(len(words) - 1):
                if words[i] not in markov_dict: markov_dict[words[i]] = []
                markov_dict[words[i]].append(words[i+1])
            if words[-1] not in markov_dict: markov_dict[words[-1]] = []
            markov_dict[words[-1]].append("__END__")
        
        save_model(markov_dict)
        print("学習が完了し、モデルファイルを保存しました。")
        
        # 2. 投稿
        generated_text = generate_sentence(markov_dict)
        if generated_text:
            await posting_channel.send(generated_text)
            print(f"メッセージを「{posting_channel.name}」に投稿しました。")
        
        # 3. ログアウト
        print("タスクが完了したため、ログアウトします。")
        await client.close()

    await client.start(TOKEN)


# --- プログラムの実行部分 ---
# --- プログラムの実行部分 ---
# ↓↓↓↓ このブロックをまるごと置き換えてください ↓↓↓↓
if __name__ == "__main__":
    print("--- SCRIPT CHECKPOINT 1: プログラム実行開始 ---")

    if not TOKEN or LEARNING_CHANNEL_ID == 0 or POSTING_CHANNEL_ID == 0:
        print("--- SCRIPT CHECKPOINT 2: 失敗（Secretsがありません） ---")
        print("エラー: 必要な情報（TOKEN, チャンネルID）が設定されていません。")
    else:
        print("--- SCRIPT CHECKPOINT 3: Secretsの読み込み成功 ---")
        # メイン処理を実行
        asyncio.run(main_task())
        # 実行後にモデルの変更をGitHubに保存
        commit_and_push_model()
        print("--- SCRIPT CHECKPOINT 4: 全ての処理が完了 ---")

# ↑↑↑↑ このブロックをまるごと置き換えてください ↑↑↑↑
