# 必要なライブラリをインポート
import discord
from discord.ext import tasks
import random
import json
import datetime
from janome.tokenizer import Tokenizer
import os

# ----------------- 設定項目 -----------------
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# Discord Developer Portalから取得したTokenに置き換えてください
TOKEN = "MTM4NTk0NzQ0MDI3NTc4Mzc2MA.GBq7kY.mUP8nN0PkeNklZmKN41yis5VhRWgthk4e-jtpg"

# 監視・学習させたいチャンネルのIDに置き換えてください
LEARNING_CHANNEL_ID = 1221447786554327061

# 毎日0時に自動投稿させたいチャンネルのIDに置き換えてください
POSTING_CHANNEL_ID = 1385952195173814323
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# 学習モデルを保存するファイル名
MODEL_PATH = "markov_model.json"
# ---------------------------------------------

# --- 初期設定 ---
# 日本時間(JST)のタイムゾーンを設定
JST = datetime.timezone(datetime.timedelta(hours=9))

# Botが必要とする権限(インテント)を設定
intents = discord.Intents.default()
intents.message_content = True

# Botのクライアントオブジェクトと、形態素解析のオブジェクトを生成
client = discord.Client(intents=intents)
t = Tokenizer()

# マルコフ連鎖の辞書を格納するグローバル変数
markov_dict = {}


# --- 関数定義 ---
# モデル（辞書）をファイルに保存する関数
def save_model():
    """マルコフ連鎖の辞書をJSONファイルとして保存します。"""
    with open(MODEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(markov_dict, f, ensure_ascii=False, indent=2)
    print("モデルをファイルに保存しました。")

# モデル（辞書）をファイルから読み込む関数
def load_model():
    """JSONファイルからマルコフ連鎖の辞書を読み込みます。"""
    global markov_dict
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'r', encoding='utf-8') as f:
            markov_dict = json.load(f)
        print("モデルをファイルから読み込みました。")
    else:
        markov_dict = {"__START__": []}
        print("モデルファイルが見つかりません。新しいモデルを作成します。")

# マルコフ連鎖に基づいて文章を生成する関数
def generate_sentence():
    """学習済みモデルから新しい文章を生成します。"""
    if not markov_dict.get("__START__"):
        return None
    
    sentence = []
    # 開始単語をランダムに選択
    current_word = random.choice(markov_dict["__START__"])
    sentence.append(current_word)

    # 2番目の単語から連鎖を開始し、最大100単語まで続ける
    for _ in range(100):
        # 次の単語の候補がない場合はそこで終了
        if current_word not in markov_dict:
            break
        
        next_word = random.choice(markov_dict[current_word])

        # 終了記号が出たら文章の完成
        if next_word == "__END__":
            break
        
        sentence.append(next_word)
        current_word = next_word
        
    return "".join(sentence)


# --- Discord Botのイベントとタスク ---
# Botの起動が完了したときに実行されるイベント
@client.event
async def on_ready():
    """Bot起動時にモデルを読み込み、定期タスクを開始します。"""
    print(f'Bot: {client.user} としてログインしました')
    load_model()
    daily_task.start()

# 毎日 日本時間の0時0分に実行される定期タスク
@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=JST))
async def daily_task():
    """毎日0時に学習と投稿を自動実行します。"""
    print(f"[{datetime.datetime.now(JST)}] 日次タスクを実行します。")
    
    # 1. 指定されたチャンネルから学習
    learning_channel = client.get_channel(LEARNING_CHANNEL_ID)
    if not learning_channel:
        print(f"エラー: 学習チャンネル(ID: {LEARNING_CHANNEL_ID})が見つかりません。")
        return
        
    print(f"「{learning_channel.name}」で学習を開始します。")
    async for msg in learning_channel.history(limit=3000): # 学習するメッセージ数
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
    
    save_model()
    print("学習が完了しました。")

    # 2. 指定されたチャンネルに投稿
    posting_channel = client.get_channel(POSTING_CHANNEL_ID)
    if not posting_channel:
        print(f"エラー: 投稿チャンネル(ID: {POSTING_CHANNEL_ID})が見つかりません。")
        return

    generated_text = generate_sentence()
    if generated_text:
        await posting_channel.send(generated_text)
        print(f"メッセージを「{posting_channel.name}」に投稿しました: {generated_text}")

# 管理者による手動コマンドを受け付けるイベント
# on_message関数を、まるごと以下に置き換えてください
# on_message関数を、まるごと以下に置き換えてください

# on_message関数を、まるごと以下に置き換えてください

@client.event
async def on_message(message):
    """メンション付きコマンドを処理します。権限はコマンドごとにチェックします。"""
    if message.author.bot:
        return

    # --- メンションの確認 ---
    is_user_mention = client.user in message.mentions
    is_role_mention = False
    if message.guild and not is_user_mention:
        bot_member = message.guild.get_member(client.user.id)
        if bot_member and any(role in bot_member.roles for role in message.role_mentions):
            is_role_mention = True
    
    if not is_user_mention and not is_role_mention:
        return

    # --- コマンドの抽出 ---
    command_text = message.content
    command_text = command_text.replace(f'<@{client.user.id}>', '')
    command_text = command_text.replace(f'<@!{client.user.id}>', '')
    for role in message.role_mentions:
        command_text = command_text.replace(f'<@&{role.id}>', '')
    
    command = command_text.strip().lower()


    # --- コマンドに応じた処理 ---
    if command == 'train':
        # 'train'コマンドの場合、管理者権限をチェック
        if not message.author.guild_permissions.administrator:
            await message.reply("`train`コマンドは管理者のみが使用できます。", mention_author=False)
            return
        
        # --- 管理者のみ実行できる学習処理 ---
        await message.reply("手動での学習を開始します...", mention_author=False)
        channel = message.channel
        print(f"管理者コマンドにより、「{channel.name}」で学習を開始します。")
        async for msg in channel.history(limit=3000):
            if msg.author.bot or msg.content.startswith(('!', '@')): continue
            words = list(t.tokenize(msg.content, wakati=True))
            if not words: continue
            if words[0] not in markov_dict["__START__"]: markov_dict["__START__"].append(words[0])
            for i in range(len(words) - 1):
                if words[i] not in markov_dict: markov_dict[words[i]] = []
                markov_dict[words[i]].append(words[i+1])
            if words[-1] not in markov_dict: markov_dict[words[-1]] = []
            markov_dict[words[-1]].append("__END__")
        save_model()
        await message.channel.send("学習が完了しました。")

    elif command == 'speak':
        # 'speak'コマンドは権限チェックなしで誰でも実行可能
        generated_text = generate_sentence()
        if generated_text:
            await message.channel.send(generated_text)
        else:
            # 誰にでも見えるメッセージなので、少し親切に
            await message.reply("ごめんなさい、まだおしゃべりの準備ができていません。管理者の人が学習させてくれるのを待っててくださいね。", mention_author=False)
    
    elif command: # メンションされたけど、コマンドが不明な場合
        # 管理者かどうかで応答を少し変える
        if message.author.guild_permissions.administrator:
            await message.reply(f"コマンド「{command}」は不明です。\n`@Bot名 train`または`@Bot名 speak`が使用できます。", mention_author=False)
        else:
            await message.reply(f"`@Bot名 speak`と話しかけてみてくださいね！", mention_author=False)
    

# --- Botの起動 ---
try:
    client.run(TOKEN)
except discord.errors.LoginFailure:
    print("エラー: 不正なDiscord Tokenです。設定項目を確認してください。")
except Exception as e:
    print(f"予期せぬエラーが発生しました: {e}")