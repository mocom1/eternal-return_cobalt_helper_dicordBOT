import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import load_db, save_db
from elo import calculate_elo

load_dotenv("token.env")

# 1. 봇 설정 및 선언 (반드시 소문자 bot)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "cobalt_db.json"

내전방_ID = 1522218958189494292
current_match = {"team_a": [], "team_b": []}



# 2. 이벤트 등록 (위에서 만든 소문자 bot을 사용)
@bot.event
async def on_ready():
    print(f"[{bot.user.name}] 봇이 성공적으로 로그인했습니다!")
    CHANNEL = bot.get_channel(내전방_ID)

    if CHANNEL is not None:
        await CHANNEL.send("봇이 정상적으로 작동 중입니다!")

####################################################################


# 3. 명령어 등록
# 6. 봇 명령어 등록: 가이드라인(도움말) 출력 기능
@bot.command(name="명령어")
async def show_commands_list(ctx):
    """봇이 제공하는 모든 명령어 안내서를 출력합니다."""
    # 지정한 내전방이 아니면 명령어를 완전히 무시합니다.
    if ctx.channel.id != 내전방_ID:
        return

    # 친구들이 보기 쉽게 이쁜 텍스트박스 형태로 설명서를 디자인함!
    help_message = (
        f"🤖 **[코발트 봇] 이용 가이드라인**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 모든 명령어는 앞에 **느낌표(!)**를 붙여서 사용합니다.\n\n"
        f"🔹 `!등록 [이터널리턴 닉네임]` : 내전 시스템에 내 프로필을 최초 등록합니다.\n"
        f"🔹 `!정보` : 내 닉네임, 전적(승/패), 승률, 현재 MMR을 조회합니다.\n"
        f"🔹 `!인원` : 등록된 모든 내전 멤버들의 닉네임, 전적을 순서대로 조회합니다.\n"
        f"🔹 `!매칭` : 현재 통화방에 입장한 인원 기준으로 MMR 균형에 맞게 팀을 반반 나눕니다.\n"
        f"🔹 `!명령어` : 현재 보고 계신 봇 사용 설명서를 다시 띄웁니다.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *지정된 내전방 채널 외에서는 봇이 응답하지 않습니다.*"
    )
    await ctx.send(help_message, silent=True)


@bot.command()
async def 테스트(ctx):
    if ctx.channel.id != 내전방_ID:
        return
    await ctx.send("discord 봇이 정상적으로 작동 중입니다!")

# 4. 봇 명령어 등록: 유저 등록 기능
@bot.command(name="등록")
async def register_user(ctx, *, ER_nickname: str = None):
    # 지정한 내전방이 아니면 명령어를 완전히 무시(컷)합니다.
    if ctx.channel.id != 내전방_ID:
        return

    # 닉네임을 안 적고 "!등록"만 쳤을 때 예외 처리
    if ER_nickname is None:
        await ctx.send("❌ 올바른 형식으로 입력해 주세요. 예시: `!등록 [이터널리턴 닉네임]`", silent=True)
        return

    # [1단계] 하드디스크에서 최신 DB 데이터를 파이썬 메모리로 가져옵니다.
    user_db = load_db()
    
    # [2단계] 명령어를 친 사람의 디스코드 고유 번호(ID)를 문자로 바꿉니다.
    user_id = str(ctx.author.id)

    # [3단계] 이미 등록된 사람인지 확인해서 튕겨냅니다.
    if user_id in user_db:
        await ctx.send(f"⚠️ 이미 등록되어 있습니다! (등록된 닉네임: {user_db[user_id]['nickname']})", silent=True)
        return

    # [4단계] 장부에 새 유저 칸을 파고 기본 데이터를 집어넣습니다.
    user_db[user_id] = {
        "nickname": ER_nickname,
        "win": 0,
        "lose": 0,
        "mmr": 1000  # 기본 MMR 점수 1000점으로 시작!
    }

    # [5단계] 변경된 파이썬 메모리 데이터를 진짜 파일(cobalt_db.json)에 저장합니다.
    save_db(user_db)
    
    # 터미널에 기록 남기고 디코방에 성공 알림 보내기
    print(f"📝 DB 등록 완료: {ctx.author.name} -> {ER_nickname}")
    await ctx.send(f"✅ {ctx.author.mention} 님의 프로필 등록이 완료되었습니다! (초기 MMR: 1000)", silent=True)

# 5. 봇 명령어 등록: 본인 정보 조회 기능
@bot.command(name="정보")
async def show_user_info(ctx):
    """명령어를 친 유저 본인의 DB 데이터를 가져와 이쁘게 출력합니다."""
    # 지정한 내전방이 아니면 명령어를 완전히 무시합니다.
    if ctx.channel.id != 내전방_ID:
        return

    # 1. 최신 데이터베이스(DB) 데이터를 불러옵니다.
    user_db = load_db()
    
    # 2. 명령어를 친 사람의 디스코드 고유 번호(ID)를 문자로 바꿉니다.
    user_id = str(ctx.author.id)

    # 3. 만약 DB에 이 사람의 ID가 없다면? (등록 안 한 사람 예외 처리)
    if user_id not in user_db:
        await ctx.send(f"❌ {ctx.author.mention} 님은 아직 등록되지 않았습니다! `!등록 [롤닉네임]`으로 먼저 등록해 주세요.", silent=True)
        return

    # 4. DB에서 이 사람의 정보 보따리를 쏙 빼옵니다.
    user_data = user_db[user_id]
    nickname = user_data["nickname"]
    win = user_data["win"]
    lose = user_data["lose"]
    mmr = user_data["mmr"]

    # 5. [승률 계산] 판수가 0판이면 승률 0%, 그 외에는 (승리 / 총판수) * 100
    total_games = win + lose
    if total_games == 0:
        win_rate = 0.0
    else:
        win_rate = (win / total_games) * 100

    # 6. 디코방에 이쁘게 정렬해서 출력하기
    # (win_rate:.1f는 소수점 첫째 짜리까지만 나오게 반올림하라는 뜻이야!)
    info_message = (
        f"📊 **{ctx.author.mention} 님의 내전 프로필**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 **닉네임:** {nickname}\n"
        f"🔥 **전적:** {win}승 {lose}패 (총 {total_games}판)\n"
        f"📈 **승률:** {win_rate:.1f}%\n"
        f"🎖️ **MMR:** {mmr} 점"
    )

    await ctx.send(info_message, silent=True)


# 7. 봇 명령어 등록: 전체 등록 인원 랭킹 리스트 출력 기능
@bot.command(name="인원")
async def show_all_users(ctx):
    """DB에 등록된 모든 유저를 MMR이 높은 순서대로 정렬하여 리스트로 출력합니다."""
    # 지정한 내전방이 아니면 명령어를 완전히 무시합니다.
    if ctx.channel.id != 내전방_ID:
        return

    # 1. 최신 데이터베이스(DB) 데이터를 불러옵니다.
    user_db = load_db()

    # 2. 만약 DB에 등록된 사람이 아무도 없다면 예외 처리
    if not user_db:
        await ctx.send("📋 현재 등록된 내전 멤버가 아무도 없습니다. `!등록`으로 첫 멤버가 되어보세요!", silent=True)
        return

    # 3. [★핵심 정렬 알고리즘] 
    # 딕셔너리에 흩어져 있는 유저들을 MMR이 높은 순서(descending)로 싹 정렬해서 리스트로 만듭니다.
    # item[1]['mmr']를 기준으로 삼아 내림차순(reverse=True) 정렬하라는 파이썬 마법의 문장이야!
    sorted_users = sorted(user_db.items(), key=lambda item: item[1]["mmr"], reverse=True)

    # 4. 리스트 문자열 조립하기
    list_message = " **코발트 내전 멤버 현황** \n"
    list_message += "━━━━━━━━━━━━━━━━━━━━\n"
    list_message += "닉네임 (전적) | MMR 점수\n"
    list_message += "━━━━━━━━━━━━━━━━━━━━\n"

    # 5. 정렬된 유저 리스트를 돌면서 1등부터 순서대로 한 줄씩 텍스트를 쌓아 올립니다.
    # enumerate(..., 1)은 등수를 1등부터 자동으로 계산해 주는 똑똑한 녀석이야!
    for rank, (user_id, info) in enumerate(sorted_users, 1):
        nickname = info["nickname"]
        win = info["win"]
        lose = info["lose"]
        mmr = info["mmr"]
        
        list_message += f"{nickname} ({win}승 {lose}패) | `{mmr}점`\n"

    list_message += "━━━━━━━━━━━━━━━━━━━━\n"

    await ctx.send(list_message, silent=True)



from itertools import combinations  # 파일 맨 위쪽에 적어도 되고, 여기에 적어도 작동합니다.
# 8. 봇 명령어 등록: 통화방 인원 기준 황금 밸런스 팀 배치 기능
@bot.command(name="매칭")
async def balance_teams(ctx):
    """명령어 사용자가 입장한 통화방 인원을 긁어와서 MMR 균형에 맞게 팀을 반반 나눕니다."""
    if ctx.channel.id != 내전방_ID:
        return

    # 1. 명령어를 친 유저가 진짜로 통화방에 들어가 있는지 확인
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("❌ 이 명령어는 음성 채널(통화방)에 입장한 상태에서만 사용할 수 있습니다!", silent=True)
        return

    voice_channel = ctx.author.voice.channel
    members = voice_channel.members  # 통화방에 앉아있는 유저 명단을 싹 긁어옴!
    total_count = len(members)

    # 2. 최소 인원 및 짝수 제약 조건 체크 (홀수면 반반 안 나눠지니까 컷!)
    if total_count < 2:
        await ctx.send("❌ 팀을 짜려면 통화방에 최소 2명 이상 있어야 합니다.", silent=True)
        return
    if total_count % 2 != 0:
        await ctx.send(f"❌ 현재 통화방 인원이 홀수({total_count}명)입니다! 팀을 반반 나눌 수 있도록 인원수를 맞춰주세요.", silent=True)
        return

    half_size = total_count // 2  # 한 팀의 크기 (6명이면 3, 8명이면 4, 10명이면 5)
    user_db = load_db()

    # 3. 통화방 인원들의 MMR 점수를 DB에서 매칭 (등록 안 된 친구면 기본 1000점으로 계산)
    match_members = []
    for m in members:
        uid = str(m.id)
        if uid in user_db:
            mmr = user_db[uid]["mmr"]
            nickname = user_db[uid]["nickname"]
        else:
            mmr = 1000  # 디비에 없는 뉴비는 기본 1000점 부여
            nickname = m.display_name  # 디스코드 서버 별명 사용
            
        match_members.append({"id": uid, "name": nickname, "mmr": mmr})

    # 4. [수학적 최적화] 두 팀의 MMR 합산 차이가 가장 적은 황금 조합 찾기
    best_diff = float('inf')
    best_team_a = []
    best_team_b = []
    
    # 전체 인원 중 정확히 절반을 뽑는 모든 경우의 수를 무한 순회
    for team_a_comb in combinations(match_members, half_size):
        team_a = list(team_a_comb)
        # 전체 명단에서 A팀에 뽑힌 사람을 제외한 나머지를 자동으로 B팀 지정
        team_b = [m for m in match_members if m not in team_a]
        
        sum_a = sum(m["mmr"] for m in team_a)
        sum_b = sum(m["mmr"] for m in team_b)
        diff = abs(sum_a - sum_b)  # 두 팀의 점수 차이 계산
        
        # 지금까지 찾은 조합보다 더 균형 잡힌 조합을 찾았다면 갱신!
        if diff < best_diff:
            best_diff = diff
            best_team_a = team_a
            best_team_b = team_b

    # 5. 최종 결정된 팀원들의 '디코드 ID'를 아까 만든 임시 상자(current_match)에 기억시킴!
    global current_match
    current_match["team_a"] = [m["id"] for m in best_team_a]
    current_match["team_b"] = [m["id"] for m in best_team_b]

    # 6. 디스코드 화면에 이쁘게 출력할 대진표 조립
    output_msg = f"⚖️ **음성 채널 [{voice_channel.name}] 기준 매칭**\n"
    output_msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    output_msg += "🔵 **A 팀**\n"
    for m in best_team_a:
        output_msg += f"• {m['name']} (`{m['mmr']}점`)\n"
   
    
    output_msg += "🔴 **B 팀**\n"
    for m in best_team_b:
        output_msg += f"• {m['name']} (`{m['mmr']}점`)\n"
    
    output_msg += "━━━━━━━━━━━━━━━━━━━━\n"
    output_msg += "💡 게임이 끝나면 승리한 팀에 맞게 명령어(`!A팀승리` 또는 `!B팀승리`)를 입력하세요."
    output_msg += "\n💡 만약 팀을 다시 짜고 싶으면 `!취소`를 입력하세요.  "

    await ctx.send(output_msg, silent=True)





# 9. 봇 명령어 등록: A팀 승리 정산 기능
@bot.command(name="A팀승리")
async def team_a_win(ctx):
    """기억된 대전 명단에서 A팀은 승리, B팀은 패배 처리하고 MMR을 정산합니다."""
    if ctx.channel.id != 내전방_ID:
        return

    # 봇 머릿속(임시 상자)에 기억된 대진 명단이 비어있는지 체크
    if not current_match["team_a"] or not current_match["team_b"]:
        await ctx.send("❌ 현재 진행 중인 내전 게임 정보가 없습니다! `!매칭`으로 팀을 먼저 짜주세요.", silent=True)
        return

    user_db = load_db()

    # 1. 양 팀의 평균 MMR 계산하기 (Elo 공식의 기준점이 됨)
    a_mmrs = [user_db[uid]["mmr"] for uid in current_match["team_a"] if uid in user_db]
    b_mmrs = [user_db[uid]["mmr"] for uid in current_match["team_b"] if uid in user_db]
    
    avg_a = sum(a_mmrs) / len(a_mmrs) if a_mmrs else 1000
    avg_b = sum(b_mmrs) / len(b_mmrs) if b_mmrs else 1000

    # 2. 🔵 A팀 (승리자들 전적 및 점수 상승 처리)
    for user_id in current_match["team_a"]:
        if user_id in user_db:
            p_data = user_db[user_id]
            total_games = p_data["win"] + p_data["lose"]
            # 우리 수학 계산기 작동! (내점수, 상대팀평균, 내판수, 20)
            new_mmr, _ = calculate_elo(p_data["mmr"], avg_b, total_games, 20)
            
            p_data["win"] += 1
            p_data["mmr"] = new_mmr

    # 3. 🔴 B팀 (패배자들 전적 및 점수 하락 처리)
    for user_id in current_match["team_b"]:
        if user_id in user_db:
            p_data = user_db[user_id]
            total_games = p_data["win"] + p_data["lose"]
            # 우리 수학 계산기 작동! (상대팀평균, 내점수, 20, 내판수)
            _, new_mmr = calculate_elo(avg_a, p_data["mmr"], 20, total_games)
            
            p_data["lose"] += 1
            p_data["mmr"] = new_mmr

    # 4. 변경된 최신 상태를 진짜 파일(DB)에 저장하고 임시 상자 초기화
    save_db(user_db)
    current_match["team_a"] = []
    current_match["team_b"] = []

    await ctx.send("🏆 **A팀의 승리로 경기가 기록되었습니다!**", silent=True)


# 10. 봇 명령어 등록: B팀 승리 정산 기능 (위와 논리는 완전히 똑같고 공수만 바뀜!)
@bot.command(name="B팀승리")
async def team_b_win(ctx):
    """기억된 대전 명단에서 B팀은 승리, A팀은 패배 처리하고 MMR을 정산합니다."""
    if ctx.channel.id != 내전방_ID:
        return

    if not current_match["team_a"] or not current_match["team_b"]:
        await ctx.send("❌ 현재 진행 중인 내전 게임 정보가 없습니다! `!매칭`으로 팀을 먼저 짜주세요.", silent=True)
        return

    user_db = load_db()

    a_mmrs = [user_db[uid]["mmr"] for uid in current_match["team_a"] if uid in user_db]
    b_mmrs = [user_db[uid]["mmr"] for uid in current_match["team_b"] if uid in user_db]
    
    avg_a = sum(a_mmrs) / len(a_mmrs) if a_mmrs else 1000
    avg_b = sum(b_mmrs) / len(b_mmrs) if b_mmrs else 1000

    # 🔵 A팀 (패배자들 처리)
    for user_id in current_match["team_a"]:
        if user_id in user_db:
            p_data = user_db[user_id]
            total_games = p_data["win"] + p_data["lose"]
            _, new_mmr = calculate_elo(avg_b, p_data["mmr"], 20, total_games)
            p_data["lose"] += 1
            p_data["mmr"] = new_mmr

    # 🔴 B팀 (승리자들 처리)
    for user_id in current_match["team_b"]:
        if user_id in user_db:
            p_data = user_db[user_id]
            total_games = p_data["win"] + p_data["lose"]
            new_mmr, _ = calculate_elo(p_data["mmr"], avg_a, total_games, 20)
            p_data["win"] += 1
            p_data["mmr"] = new_mmr

    save_db(user_db)
    current_match["team_a"] = []
    current_match["team_b"] = []

    await ctx.send("🏆 **B팀의 승리로 경기가 기록되었습니다!**", silent=True)


# 11. 봇 명령어 등록: 현재 매칭된 팀 정보 취소(리셋) 기능
@bot.command(name="취소")
async def cancel_match(ctx):
    """현재 `!매칭`으로 임시 저장된 대진표 정보를 싹 비우고 초기화합니다."""
    if ctx.channel.id != 내전방_ID:
        return

    global current_match

    # 1. 이미 비어있는데 취소하라고 하면 안내 메시지 출력
    if not current_match["team_a"] and not current_match["team_b"]:
        await ctx.send("❓ 현재 대기 중인 내전 게임 정보가 이미 없습니다! 취소할 대진표가 없어요.", silent=True)
        return

    # 2. 임시 저장 상자를 싹 비워서 리셋하기 (대청소🧹)
    current_match["team_a"] = []
    current_match["team_b"] = []

    # 3. 디비(파일)는 건드리지 않았으니, 대진표만 취소되었다고 안심시켜 주기
    await ctx.send("🧹 **현재 대진표가 취소되었습니다!**\n유저들의 전적과 MMR은 안전하며, 팀을 다시 짜려면 `!매칭`를 입력해 주세요.", silent=True)

# 4. 봇 실행 (여기에 네 토큰 박기!)
bot.run(os.getenv("DISCORD_TOKEN"))

#실행명령어 : python main.py