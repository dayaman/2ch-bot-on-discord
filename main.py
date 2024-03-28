import discord
import discord.ext.commands
from discord import Interaction, ui, TextStyle
import yaml
import datetime
import hashlib
from model import MyDatabase

intents = discord.Intents.default()
intents.typing = False
intents.guild_messages = True
intents.presences = False
intents.guilds = True

# database接続
db = MyDatabase('database.db')

class MyHelpCommand(discord.ext.commands.HelpCommand):
    def __init__(self):
        super().__init__(
            show_hidden=False,
            command_attrs={"brief": "ヘルプを表示"}
        )
    
    async def send_bot_help(self, mapping):
        await self.get_destination().send("""
        このコマンドは「2ch」「5ch」と言う名前のチャンネルで使えます。
        コマンド一覧
        /2ch : 投稿フォームが表示され、匿名で投稿ができます。
        /name [名前] : デフォルトの名前を更新します。
        /help : このヘルプを表示します。
                                                    
        投稿フォームについて
        名前：名前を入力します。名前は省略できます。名前の後に#をつけてパスワードを入力するとトリップが生成されます。(例: hoge#password -> hoge◆trip)
        本文：投稿内容を入力します。                                     
        """)

bot = discord.ext.commands.Bot(command_prefix="/", help_command=MyHelpCommand(),intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()

@bot.event
async def on_guild_available(guild):
    await tree.sync(guild=discord.Object(id=guild.id))
    # guild.idがデータベースになければ、データベースに追加
    if db.select_name(guild.id) is None:
        db.insert_data(guild.id)

    # 2ch か 5ch という名前のチャンネルがなければ作成
    if discord.utils.get(guild.channels, name="2ch") is None:
        await guild.create_text_channel("2ch")

@bot.event
async def on_guild_join(guild):
    await tree.sync(guild=discord.Object(id=guild.id))
    # guild.idがデータベースになければ、データベースに追加
    if db.select_name(guild.id) is None:
        db.insert_data(guild.id)
    
    # 2ch か 5ch という名前のチャンネルがなければ作成
    if discord.utils.get(guild.channels, name="2ch") is None:
        await guild.create_text_channel("2ch")

@bot.event
async def on_guild_remove(guild):
    # guild.idがデータベースにあれば、データベースから削除
    if db.select_name(guild.id) is not None:
        db.delete_data(guild.id)

def create_res(name, text, interaction):
    # name に#が含まれている場合、その前後で分割して、前の部分を名前として使う。後ろの部分はpasswordに格納する
    # 例: "名前#password" という文字列が入力された場合、名前は "名前" 、passwordは "password" となる
    # 例: "名前" という文字列が入力された場合、名前は "名前" 、passwordは "" となる
    # 例: "名前#" という文字列が入力された場合、名前は "名前" 、passwordは "" となる
    # 例: "名前#password#password2" という文字列が入力された場合、名前は "名前" 、passwordは "password#password2" となる
    if "#" in name:
        name, password = name.split("#", 1)
    else:
        password = ""

    # name が空の場合はデフォルトの名前を使う
    if name == "":
        name = db.select_name(interaction.guild.id)[0]

    # ID作成
    user_id = interaction.user.id
    hashed_id = hashlib.md5((str(datetime.date.today()) + str(user_id)).encode()).hexdigest()[:6]

    # trip作成
    if name != "" and password != "":
        trip = hashlib.md5(password.encode()).hexdigest()[:8]
        name = f"{name}◆{trip}"
        hashed_id = "??????"
    elif name != "":
        name = name.replace('◆', '◇')

    # fusianasanを実装
    if name == "fusianasan":
        name = interaction.user.name
    
    # YYYY/MM/DD HH:MM:SSの形式で現在時刻を取得
    now = datetime.datetime.now()
    nowdt = now.strftime("%Y/%m/%d %H:%M:%S")

    # データベースからカウントを取得
    count = db.select_count(interaction.guild.id)[0]

    title_template = f"**{count} 名前：{name} : {nowdt} ID:{hashed_id}**"

    # カウントを1増やす
    db.update_count(interaction.guild.id)

    return f"{title_template}\n{text}"
    


class PostModal(ui.Modal, title="投稿フォーム"):
    def __init__(self, default_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(ui.TextInput(label="name", placeholder=default_name, required=False))
        self.add_item(ui.TextInput(label="本文", placeholder="ここに本文を入力", style=TextStyle.long))

    async def on_submit(self, interaction: Interaction):
        await interaction.response.send_message("レスしました", ephemeral=True, delete_after=5)

        await interaction.channel.send(create_res(self.children[0].value, self.children[1].value, interaction))
        return

@bot.hybrid_command(name='2ch', description="匿名で2ch風の投稿をします")
async def post(ctx):
    if ctx.channel.name != "2ch" and ctx.channel.name != "5ch":
        ctx.interaction.response.send_message("このチャンネルではつかえません", ephemeral=True)
        return
    # データベースからデフォルトの名前を取得
    default_name = db.select_name(ctx.guild.id)[0]
    modal = PostModal(default_name)
    await ctx.interaction.response.send_modal(modal)

# default_nameを更新するコマンド
@bot.hybrid_command(name='name', description="名前を更新します")
async def update_name(ctx, name: str):
    db.update_name(ctx.guild.id, name)
    await ctx.interaction.response.send_message(f"名前を {name} に更新しました", ephemeral=True)

# Read bot token from config.yml
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    bot_token = config['bot_token']

bot.run(bot_token)
