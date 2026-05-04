import streamlit as st
from openai import OpenAI
import re
import random
import json
import os

# --- 页面基础配置 ---
st.set_page_config(page_title="高冷仙子通通变成齁哦哦哦的母猪", layout="wide")

# --- 全新优化高级感UI ---
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 50% 50%, #1e123d 0%, #0f091f 100%);
    color: #f0f0ff;
}

h1 {
    background: linear-gradient(120deg, #d4a5ff, #9d6fff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900 !important;
}

[data-testid="stSidebar"] {
    background-color: #0d071d !important;
    border-right: 1px solid #3d2b6d !important;
}

.stTextInput input, .stTextArea textarea, .stNumberInput input, [data-baseweb="select"] > div {
    background-color: rgba(36, 24, 71, 0.8) !important;
    border: 1px solid #5a4a9f !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7e57c2 0%, #5e35b1 100%) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px 0 rgba(0,0,0,0.3) !important;
    transition: transform 0.1s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(126, 87, 194, 0.3) !important;
    color: #fff !important;
    border: none !important;
}

.stChatMessage {
    background-color: rgba(42, 29, 82, 0.4) !important;
    border-radius: 15px !important;
    margin: 10px 0 !important;
    border: 1px solid rgba(90, 74, 159, 0.3) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(4px) !important;
}

/* 聊天输入框美化 */
[data-testid="stChatInput"] {
    border: 1px solid #5e35b1 !important;
    border-radius: 15px !important;
    background-color: #140b29 !important;
}

.stTabs button {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #b39ddb !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background-color: #9575cd !important;
}

.stAlert {
    background-color: rgba(42, 29, 82, 0.8) !important;
    color: #f0e6ff !important;
    border: 1px solid #5e35b1 !important;
}

.stMultiSelect [data-baseweb="tag"] {
    background-color: #5e35b1 !important;
}

hr {
    border: 0;
    height: 1px;
    background: linear-gradient(to right, rgba(126, 87, 194, 0), rgba(126, 87, 194, 0.5), rgba(126, 87, 194, 0));
}

.main .block-container {
    padding-bottom: 80px !important;
    padding-top: 30px !important;
}

/* 调整侧边栏弹出按钮位置，避免与手机状态栏重叠 */
/* 更可靠的定位方式，确保按钮向下移动 */
[data-testid="stSidebarToggleButton"] {
    position: fixed !important; /* 确保是固定定位 */
    top: 300px !important; /* 调整此值以避开状态栏，例如60px-80px */
    left: 50px !important; /* 可以根据需要微调左右位置 */
}
</style>
""", unsafe_allow_html=True)

# --- 全局生成控制状态 ---
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "stop_signal" not in st.session_state:
    st.session_state.stop_signal = False

# --- 数据持久化 ---
CONFIG_FILE = "config.json"
SAVES_FILE = "saves.json"
TOKEN_FILE = "token_usage.json"

def load_data(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_data(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 初始化状态 ---
cfg = load_data(CONFIG_FILE, {})
if "story_history" not in st.session_state:
    st.session_state.story_history = []
if "current_context" not in st.session_state:
    st.session_state.current_context = cfg.get("context", {
        "genre": "玄幻", "name": "", "gender": "男", "age": 18,
        "origin": "", "appearance": "", "traits": [], "background": "", "skills": ""
    })
if "memory" not in st.session_state:
    st.session_state.memory = "暂无重要剧情记忆。"
if "memory_slots" not in st.session_state:
    st.session_state.memory_slots = []
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "world_book" not in st.session_state:
    st.session_state.world_book = cfg.get("world_book", {})
if "api_key" not in st.session_state:
    st.session_state.api_key = cfg.get("api_key", "")
if "base_url" not in st.session_state:
    st.session_state.base_url = cfg.get("base_url", "https://ai.ttk.homes/v1")
if "model_name" not in st.session_state:
    st.session_state.model_name = cfg.get("model_name", "gemini-3-flash-preview-cli")
if "characters_data" not in st.session_state:
    st.session_state.characters_data = cfg.get("characters_data", {})
if "general_prefix" not in st.session_state:
    st.session_state.general_prefix = cfg.get("general_prefix", "")
if "trait_pool" not in st.session_state:
    st.session_state.trait_pool = []

# Token 记录
if "token_usage" not in st.session_state:
    st.session_state.token_usage = load_data(TOKEN_FILE, {
        "total_prompt_tokens": 0, "total_completion_tokens": 0, "total_tokens": 0, "history": []
    })
# 大纲约束
if "outline_constraint" not in st.session_state:
    st.session_state.outline_constraint = cfg.get("outline_constraint", "")
if "outline_level" not in st.session_state:
    st.session_state.outline_level = cfg.get("outline_level", 3)
if "outline_read_counter" not in st.session_state:
    st.session_state.outline_read_counter = 0

# --- API 连通性检测 ---
def check_api_connection():
    try:
        client = OpenAI(
            api_key=st.session_state.api_key,
            base_url=st.session_state.base_url
        )
        client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10,
            timeout=10
        )
        return True, "✅ API 连接成功！密钥、端点、模型均正常"
    except Exception as e:
        return False, f"❌ 连接失败：{str(e).splitlines()[0]}" # 只取错误信息的第一行，更简洁

# --- 核心逻辑 ---
def get_optimized_prompt(user_input, is_initial=False):
    ctx = st.session_state.current_context
    history = st.session_state.story_history
    search_scope = user_input + (history[-1]['content'] if history else "")
    
    relevant_chars = []
    for name, data in st.session_state.characters_data.items():
        if name in search_scope or is_initial:
            desc_cut = data['desc'][:120]
            relevant_chars.append(f"{name}(好感:{data['favor']},{data['status']}):{desc_cut}")
    char_str = "【当前人物】: " + " / ".join(relevant_chars) if relevant_chars else ""
    
    events = [f"{k}:{v[:100]}" for k, v in st.session_state.world_book.items() if k in search_scope]
    world_str = "【世界设定】: " + " | ".join(events) if events else ""

    if is_initial:
        return f"【新剧本】{ctx['genre']} | 主角:{ctx['name']}({ctx['gender']},{ctx['age']}岁)\n气运:{'|'.join(ctx['traits'])}\n出身:{ctx['origin']}\n背景:{ctx['background']}\n开场动作:{user_input}"
    else:
        long_mem = " -> ".join(st.session_state.memory_slots[-2:])
        return f"【前情】:{long_mem}\n【目前记忆】:{st.session_state.memory}\n{char_str}\n{world_str}\n行动:{user_input}"

# ====================== 修复：生成逻辑BUG（核心解决无法输出问题） / 优化：确保AI遵守所有约束 ======================
def generate_story(action_input, is_initial=False):
    if st.session_state.is_generating:
        return

    st.session_state.is_generating = True
    st.session_state.stop_signal = False

    # 获取当前上下文，用于构建Prompt
    ctx = st.session_state.current_context


    ctx = st.session_state.current_context
    st.session_state.outline_read_counter += 1
    outline_text = ""
    if st.session_state.outline_constraint.strip() and st.session_state.outline_read_counter % 3 == 0:
        level = st.session_state.outline_level
        if level == 5:
            outline_rule = "**严格遵守大纲**，100%贴合剧情走向，不允许偏离"
        elif level == 4:
            outline_rule = "紧密贴合大纲，允许少量细节自由发挥"
        elif level == 3:
            outline_rule = "遵循大纲主线，可自由扩展支线情节"
        elif level == 2:
            outline_rule = "参考大纲方向，以自由创作为主，可适度偏离"
        else:
            outline_rule = "仅作为微弱参考，完全随机创作，无需遵循大纲"
        outline_text = f"\n【大纲约束】{outline_rule}\n大纲内容：{st.session_state.outline_constraint}"

    system_prompt = f"""你是一个文笔生活化、口语化且风格直接、露骨的成人小说家，直接表现成年男女的色情部位名词。
**【核心创作原则】**：
1. **绝不能违背世界设定**：严格遵循提供的【背景设定】。
2. **绝不能违背系统提示词**：严格遵守本【任务要求】中的所有指令。
3. **绝不能违背核心前置词**：严格遵守【Rule】中的内容。

[Skill]: {ctx.get('skills', '无')}
[Rule]: {st.session_state.general_prefix}
任务要求：
1. 文风直接、露骨的成人小说家。内容需极具性张力，描写直白，如大鸡巴，大逼，小穴，乳头等词。
2. **内容平衡**：色情描写与修仙、修炼、战斗、权谋、天道等内容的比例严格保持为 1:1。绝不能削弱修仙世界的剧情发展、境界提升与宏大叙事。
3. **严格执行攻略规则**：务必检查当前登场女角色的描述与好感度。仅允许在好感度对应的范围内发生互动，好感度增加符合逻辑。
4. **违规惩罚**：若玩家尝试越级互动（如好感度不足时尝试性行为），角色必须表现出强烈反感、拒绝或羞辱，并扣除 5-10 点好感度。若符合好感阶梯，好感度单次变动上限为 +4。
5. 每次结尾生成 3 条纯文字形式的【玩家下一步动作】，具体会导致如何不生成，要保证主角发育节奏缓慢。
6. 每次结尾更新状态标签：
[记忆更新] (一句话总结当前关键进展)
[好感度更新] (格式：角色|变动数值|身体行为状态)"""

    prompt = get_optimized_prompt(action_input, is_initial) + f"\n【背景设定】:{ctx['background']}" # 确保背景设定始终在Prompt中
    final_system_prompt = system_prompt + outline_text

    full_text = ""
    display_content = ""
    try:
        client = OpenAI(api_key=st.session_state.api_key, base_url=st.session_state.base_url)
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "system", "content": final_system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=8000, # 进一步增加max_tokens，最大程度避免API端截断
            stream=True
        )

        with st.chat_message("assistant"):
            placeholder = st.empty()
            for chunk in response:
                if st.session_state.stop_signal:
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content: # 简化判断，delta.content为None时即为空
                    full_text += delta.content
                    # 优化流式显示时的截断逻辑，只在完整标签出现时才截断
                    temp_display = full_text
                    for tag_prefix in ["\[记忆更新\]", "\[好感度更新\]"]:
                        if re.search(tag_prefix, temp_display):
                            temp_display = re.split(tag_prefix, temp_display)[0]
                    display_content = temp_display
                    placeholder.markdown(display_content + " ▌")

            final_display = display_content if display_content.strip() else "（AI未能生成有效内容或生成已停止）"
            placeholder.markdown(final_display)

        if not st.session_state.stop_signal and display_content.strip():
            mem_match = re.search(r'\[记忆更新\][:：]?\s*(.*?)(?=\[|$)', full_text, re.S)
            fav_match = re.search(r'\[好感度更新\][:：]?\s*(.*?)(?=\[|$)', full_text, re.S)

            if mem_match:
                st.session_state.memory = mem_match.group(1).strip()
            if fav_match:
                for line in fav_match.group(1).strip().split('\n'):
                    parts = line.split('|')
                    if len(parts) >= 3 and parts[0] in st.session_state.characters_data:
                        name = parts[0]
                        st.session_state.characters_data[name]['favor'] += int(parts[1])
                        st.session_state.characters_data[name]['status'] = parts[2]

            st.session_state.story_history.append({"role": "assistant", "content": final_display})
            st.session_state.gen_count += 1
            if st.session_state.gen_count % 5 == 0:
                st.session_state.memory_slots.append(st.session_state.memory)
                if len(st.session_state.memory_slots) > 5:
                    st.session_state.memory_slots.pop(0)

    except Exception as e:
        st.error(f"API 调用失败: {str(e)}")
    finally:
        st.session_state.is_generating = False
        st.session_state.stop_signal = False
        st.rerun()

# --- 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 创作控制台")
    with st.expander("📊 Token 使用统计", expanded=True):
        st.markdown(f"**请求次数**: {st.session_state.gen_count}")
        st.markdown(f"**输入Token**: {st.session_state.token_usage['total_prompt_tokens']}")
        st.markdown(f"**输出Token**: {st.session_state.token_usage['total_completion_tokens']}")
        st.markdown(f"**总计Token**: {st.session_state.token_usage['total_tokens']}")
    
    t_cfg, t_char, t_world, t_outline = st.tabs(["核心配置", "人物管理", "世界/存档", "📝 大纲约束"])
    
    with t_cfg:
        st.subheader("🔌 API 基础配置")
        st.session_state.base_url = st.text_input(
            "端点 URL (API 地址/反代)",
            value=st.session_state.base_url,
            help="例如：https://api.openai.com/v1",
            disabled=st.session_state.is_generating
        )
        st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key, type="password", disabled=st.session_state.is_generating)
        st.session_state.model_name = st.text_input("模型名称", value=st.session_state.model_name, disabled=st.session_state.is_generating)

        if st.button("🔍 测试 API 连接", disabled=st.session_state.is_generating):
            with st.spinner("检测中..."):
                ok, msg = check_api_connection()
                st.success(msg) if ok else st.error(msg)

        st.divider()
        st.subheader("🖋️ 写作 Skill")
        st.session_state.current_context['skills'] = st.text_area("Skill 内容", value=st.session_state.current_context.get('skills', ''), height=100, disabled=st.session_state.is_generating)
        st.session_state.general_prefix = st.text_area("通用前置词 (Rule)", value=st.session_state.general_prefix, height=100, disabled=st.session_state.is_generating)
        if st.button("💾 保存配置", disabled=st.session_state.is_generating):
            save_data(CONFIG_FILE, {
                "api_key": st.session_state.api_key, "base_url": st.session_state.base_url,
                "model_name": st.session_state.model_name, "context": st.session_state.current_context,
                "world_book": st.session_state.world_book, "general_prefix": st.session_state.general_prefix,
                "characters_data": st.session_state.characters_data,
                "outline_constraint": st.session_state.outline_constraint,
                "outline_level": st.session_state.outline_level
            })
            st.success("配置已保存")

    with t_char:
        st.subheader("👥 人物编辑器")
        with st.expander("✨ 新增角色"):
            new_n = st.text_input("姓名", key="new_n", disabled=st.session_state.is_generating)
            new_d = st.text_area("设定", key="new_d", disabled=st.session_state.is_generating)
            if st.button("确认录入", disabled=st.session_state.is_generating):
                if new_n:
                    st.session_state.characters_data[new_n] = {"desc": new_d, "favor": 0, "status": "初见"}
                    st.rerun()
        st.divider()
        for name, data in list(st.session_state.characters_data.items()):
            with st.expander(f"👤 {name} (好感:{data['favor']})"):
                new_desc = st.text_area("描述", value=data['desc'], key=f"edit_desc_{name}", disabled=st.session_state.is_generating)
                new_status = st.text_input("状态", value=data['status'], key=f"edit_stat_{name}", disabled=st.session_state.is_generating)
                c1, c2 = st.columns([2,1])
                new_favor = c1.number_input("好感度", value=int(data['favor']), key=f"edit_fav_{name}", disabled=st.session_state.is_generating)
                if c1.button(f"✅ 保存", key=f"save_{name}", disabled=st.session_state.is_generating):
                    st.session_state.characters_data[name] = {"desc": new_desc, "favor": new_favor, "status": new_status}
                    st.toast(f"{name} 已保存")
                    st.rerun()
                if c2.button(f"🗑️ 删除", key=f"del_{name}", disabled=st.session_state.is_generating):
                    del st.session_state.characters_data[name]
                    st.rerun()

    with t_world:
        st.subheader("📖 世界书 & 存档")
        with st.expander("词条管理"):
            wk = st.text_input("关键词", disabled=st.session_state.is_generating)
            wv = st.text_area("设定", disabled=st.session_state.is_generating)
            if st.button("添加词条", disabled=st.session_state.is_generating):
                st.session_state.world_book[wk] = wv
                st.rerun()
            for k in list(st.session_state.world_book.keys()):
                if st.button(f"❌ 删除:{k}", disabled=st.session_state.is_generating):
                    del st.session_state.world_book[k]
                    st.rerun()
        st.divider()
        st.subheader("💾 存档")
        save_name = st.text_input("存档名", disabled=st.session_state.is_generating)
        if st.button("📥 保存进度", disabled=st.session_state.is_generating):
            if save_name.strip():
                all_saves = load_data(SAVES_FILE, {})
                all_saves[save_name] = {
                    "history": st.session_state.story_history, "context": st.session_state.current_context,
                    "chars": st.session_state.characters_data, "memory": st.session_state.memory,
                    "slots": st.session_state.memory_slots, "gen": st.session_state.gen_count,
                    "world_book": st.session_state.world_book, "general_prefix": st.session_state.general_prefix,
                    "outline_constraint": st.session_state.outline_constraint, "outline_level": st.session_state.outline_level
                }
                save_data(SAVES_FILE, all_saves)
                st.success(f"「{save_name}」已保存")
        all_saves = load_data(SAVES_FILE, {})
        if all_saves:
            st.subheader("📂 读档")
            selected = st.selectbox("选择存档", list(all_saves.keys()), disabled=st.session_state.is_generating)
            col1, col2 = st.columns(2)
            if col1.button("✅ 读取", disabled=st.session_state.is_generating):
                data = all_saves[selected]
                st.session_state.story_history = data["history"]
                st.session_state.current_context = data["context"]
                st.session_state.characters_data = data["chars"]
                st.session_state.memory = data["memory"]
                st.session_state.memory_slots = data["slots"]
                st.session_state.gen_count = data["gen"]
                st.session_state.world_book = data["world_book"]
                st.session_state.general_prefix = data["general_prefix"]
                st.session_state.outline_constraint = data["outline_constraint"]
                st.session_state.outline_level = data["outline_level"]
                st.success(f"已读取「{selected}」")
                st.rerun()
            if col2.button("🗑️ 删除", disabled=st.session_state.is_generating):
                del all_saves[selected]
                save_data(SAVES_FILE, all_saves)
                st.rerun()

    with t_outline:
        st.subheader("📝 剧情大纲")
        st.markdown("等级越高 = 越贴合大纲")
        st.session_state.outline_constraint = st.text_area("大纲内容", value=st.session_state.outline_constraint, height=200, disabled=st.session_state.is_generating)
        st.session_state.outline_level = st.slider("约束等级", 1,5, st.session_state.outline_level, disabled=st.session_state.is_generating)
        if st.button("💾 保存大纲", disabled=st.session_state.is_generating):
            save_data(CONFIG_FILE, {
                "api_key": st.session_state.api_key, "base_url": st.session_state.base_url,
                "model_name": st.session_state.model_name, "context": st.session_state.current_context,
                "world_book": st.session_state.world_book, "general_prefix": st.session_state.general_prefix,
                "characters_data": st.session_state.characters_data,
                "outline_constraint": st.session_state.outline_constraint,
                "outline_level": st.session_state.outline_level
            })
            st.success("大纲已保存")

# --- 主界面 ---
st.title("✍️ 修仙小说创作系统")

# 生成中状态
if st.session_state.is_generating:
    col1, col2 = st.columns([3,1])
    with col1:
        st.info("⏳ 正在生成中，请勿操作...")
    with col2:
        if st.button("🛑 停止生成", type="primary"):
            st.session_state.stop_signal = True
            st.session_state.is_generating = False
            st.rerun()

# 初始创建角色
if not st.session_state.story_history:
    st.info("请先创建主角，再开启故事")
    ctx = st.session_state.current_context
    c1,c2,c3 = st.columns(3)
    ctx['name'] = c1.text_input("主角姓名", value=ctx['name'], disabled=st.session_state.is_generating)
    ctx['genre'] = c2.selectbox("故事背景", ["玄幻修仙","赛博朋克","末日荒野","都市欲望","西幻魔法"], disabled=st.session_state.is_generating)
    ctx['age'] = c3.number_input("年龄", value=ctx['age'], disabled=st.session_state.is_generating)
    ctx['origin'] = st.text_area("主角出身", value=ctx['origin'], disabled=st.session_state.is_generating)
    ctx['background'] = st.text_area("世界背景", value=ctx['background'], disabled=st.session_state.is_generating)
    
    if st.button("🎲 随机气运", disabled=st.session_state.is_generating):
        st.session_state.trait_pool = random.sample([
            "【凡品·体弱多病】", "【凡品·傲娇】", "【仙品·悟性逆天】", "【凡品·食量惊人】",
            "【上品·书法大成】", "【良品·声音好听】", "【仙品·天龙神体】", "【良品·身体强壮】",
            "【凡品·性格孤僻】", "【上品·天煞孤星】", "【上品·过目不忘】", "【凡品·话痨】",
            "【仙品·古神圣体】", "【凡品·家徒四壁】", "【上品·炼器大师】", "【良品·精力旺盛】",
            "【凡品·穷鬼】", "【良品·认路达人】", "【良品·手脚麻利】", "【上品·易容大师】",
            "【良品·语言达人】", "【仙品·幽冥真实神髓】", "【良品·跑得快】", "【良品·厨艺精湛】",
            "【良品·第六感】", "【良品·不易生病】", "【上品·百毒不侵】"
        ],6)
    
    if st.session_state.trait_pool:
        ctx['traits'] = st.multiselect("挑选三个气运", st.session_state.trait_pool, max_selections=3, disabled=st.session_state.is_generating)
        
    if st.button("🚀 开启篇章", disabled=st.session_state.is_generating):
        if ctx['name'] and len(ctx['traits']) ==3:
            st.session_state.story_history = []
            st.session_state.gen_count = 0
            generate_story("故事开启，交代当前处境和初始互动", is_initial=True)

# 显示对话历史
for msg in st.session_state.story_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入
user_input = st.chat_input("输入你的行动...", disabled=st.session_state.is_generating)
if user_input and not st.session_state.is_generating:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.story_history.append({"role":"user","content":user_input})
    generate_story(user_input)
