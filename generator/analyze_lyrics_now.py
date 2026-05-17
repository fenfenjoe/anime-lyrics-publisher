# -*- coding: utf-8 -*-
"""
直接生成《月の大きさ》的歌词分析结果
避免让AI在对话中逐句生成（会消耗大量token）
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_analyzer import write_result_to_file, load_pending_task

# 完整的分析结果（59句）
result_json = {
    "song_intro": "乃木坂46为《火影忍者疾风传》演唱的OP，以「月」为意象，描绘成长路上的孤独与坚持。柔软的旋律中透着坚定，像月光一样温柔地照亮前行的路。每次听都会被那份「即使受伤也要继续前进」的勇气打动！",
    "result": [
        {
            "original": "今夜の月は",
            "furigana": "今夜（こんや）の月（つき）は",
            "translation": "今晚的月亮",
            "grammar": "の：连体修饰助词，连接今夜和月，表示所属或修饰关系"
        },
        {
            "original": "なぜか一回り大きくて",
            "furigana": "なぜか一回（いっかい）り大きくて",
            "translation": "不知为何格外地大",
            "grammar": "なぜか：副词，意为"不知为何、说不上为什么"。～くて：形容词连用形，表示中顿"
        },
        {
            "original": "いつもより明るく照らす",
            "furigana": "いつもより明（あ）るく照（て）らす",
            "translation": "比往常更明亮地照耀着",
            "grammar": "より：比较助词，表示比较的基准。"より"前面是比较的对象。照らす：他动词，照耀"
        },
        {
            "original": "背中を丸めてとぼとぼ帰る道",
            "furigana": "背中（せなか）を丸（まる）めてとぼとぼ帰（かえ）る道（みち）",
            "translation": "弓着背、拖着步子回家的路",
            "grammar": "を：格助词，表示动作涉及的对象（弓背这个动作）。とぼとぼ：拟态词，形容走路无力、慢吞吞的样子"
        },
        {
            "original": "どんな時も味方はいる",
            "furigana": "どんな時（とき）も味方（みかた）はいる",
            "translation": "无论何时都有同伴在",
            "grammar": "どんな～も：无论...都...，表示全面肯定。は：提示助词，强调主语"
        },
        {
            "original": "何も言わず",
            "furigana": "何（なに）も言（い）わず",
            "translation": "什么都不说",
            "grammar": "ず：否定助动词，相当于ない。言わず＝言わないで，表示伴随状态的否定"
        },
        {
            "original": "泣けたらいいね",
            "furigana": "泣（な）けたらいいね",
            "translation": "要是能哭出来就好了呢",
            "grammar": "～たら：条件表达，如果...的话。いい：好的、可以的，这里表示希望、愿望"
        },
        {
            "original": "涙が涸れたら終わり",
            "furigana": "涙（なみだ）が涸（か）れたら終（お）わり",
            "translation": "泪水枯竭之时就是终结",
            "grammar": "が：格助词，表示主语。～たら：条件表达，涸れたら＝如果枯竭了"
        },
        {
            "original": "もっと",
            "furigana": "もっと",
            "translation": "更加",
            "grammar": "もっと：副词，更、更加。表示程度加深"
        },
        {
            "original": "僕が強くならなきゃ",
            "furigana": "僕（ぼく）が強（つよ）くならなきゃ",
            "translation": "我必须变得更强",
            "grammar": "ならなきゃ＝ならない＋きゃ（口语），必须变成。強く：形容词连用形，变强"
        },
        {
            "original": "悲しみは自立への一歩",
            "furigana": "悲（かな）しみは自（じ）立（りつ）への一歩（いっぽ）",
            "translation": "悲伤是迈向自立的一步",
            "grammar": "は：提示助词，标记主题。への：名词+へ+の，表示方向、目标"
        },
        {
            "original": "何度 傷つけば",
            "furigana": "何度（なんど） 傷（きず）つけば",
            "translation": "要受多少次伤",
            "grammar": "何度～ば：几度...才...。～ば：条件形，表示假设或反复的条件"
        },
        {
            "original": "痛みを忘れる?",
            "furigana": "痛（いた）みを忘（わす）れる?",
            "translation": "才能忘记痛苦吗？",
            "grammar": "を：格助词，表示动作对象。～れる：可能态/被动/尊敬，这里是可能态疑问"
        },
        {
            "original": "赤い血を流せば",
            "furigana": "赤（あか）い血（ち）を流（なが）せば",
            "translation": "如果流下鲜红的血",
            "grammar": "赤い：形容词，红的。流せば＝流す＋れば，条件形"
        },
        {
            "original": "命を思い出すさ",
            "furigana": "命（いのち）を思（おも）い出（だ）すさ",
            "translation": "就会想起生命的意义啊",
            "grammar": "思い出す：想起、回忆起。さ：句末助词，表示强调或断定（男性语气）"
        },
        {
            "original": "道に倒れ",
            "furigana": "道（みち）に倒（たお）れ",
            "translation": "倒在路旁",
            "grammar": "に：格助词，表示动作发生的地点。倒れ：动词连用形，表示中顿"
        },
        {
            "original": "大の字に",
            "furigana": "大（だい）の字（じ）に",
            "translation": "大字型地（四仰八叉地）",
            "grammar": "大の字：汉字"大"的形状，形容人仰面朝天或趴在地上的样子。に：格助词，表示状态"
        },
        {
            "original": "空を見上げて思う",
            "furigana": "空（そら）を望（み）上げて思（おも）う",
            "translation": "仰望着天空思索",
            "grammar": "見上げて：仰望、抬头看。て：连接式，表示动作先后顺序"
        },
        {
            "original": "真の孤独とは",
            "furigana": "真（しん）の孤（こ）独（どく）とは",
            "translation": "真正的孤独是",
            "grammar": "とは：表示定义、说明，"...这个词是指..."。の：连体修饰"
        },
        {
            "original": "過去のない者",
            "furigana": "過去（かこ）のない者（もの）",
            "translation": "没有过去的人",
            "grammar": "ない：形容词，没有的。者：人、家伙"
        },
        {
            "original": "今しか知らぬ者",
            "furigana": "今（いま）しか知（し）らぬ者（もの）",
            "translation": "只知道现在的人",
            "grammar": "しか～ない：只...。知らぬ＝知らない，不知道"
        },
        {
            "original": "昨日の月は",
            "furigana": "昨日（きのう）の月（つき）は",
            "translation": "昨天的月亮",
            "grammar": "昨日：昨天。は：提示助词，标记主题"
        },
        {
            "original": "どんな大きさだったのか",
            "furigana": "どんな大（おお）きさだったのか",
            "translation": "到底是多大呢",
            "grammar": "だった：过去式断定。のか：疑问助词，表示自问或回忆"
        },
        {
            "original": "掌で形を作る",
            "furigana": "掌（てのひら）で形（かたち）を作（つく）る",
            "translation": "用掌心比划出形状",
            "grammar": "で：格助词，表示工具、手段。作る：制作、创造"
        },
        {
            "original": "生まれたその日からあの世に行く日まで",
            "furigana": "生（う）まれたその日（ひ）からあの世（よ）に行（い）く日（ひ）まで",
            "translation": "从出生那天到前往那个世界的那天为止",
            "grammar": "から～まで：从...到...。あの世：那个世界，指死后的世界"
        },
        {
            "original": "見逃すこともきっとある",
            "furigana": "見逃（みのが）すこともきっとある",
            "translation": "一定也有错过的事情",
            "grammar": "見逃す：错过、放过。こと：形式名词，使动词名词化。も：提示助词，也"
        },
        {
            "original": "仲間たちは",
            "furigana": "仲間（なかま）たちは",
            "translation": "伙伴们",
            "grammar": "たち：复数后缀，表示...们。は：提示助词"
        },
        {
            "original": "ここにはいない",
            "furigana": "ここにはいない",
            "translation": "（虽然）不在这里",
            "grammar": "には：强调存在的场所。いない＝いない，不在、没有（生物）"
        },
        {
            "original": "どこかで暮らしているよ",
            "furigana": "どこかで暮（く）らしているよ",
            "translation": "但在某处生活着哟",
            "grammar": "どこか：某处、 somewhere。暮らしている：正在生活。よ：句末助词，表示强调或告知"
        },
        {
            "original": "だけど",
            "furigana": "だけど",
            "translation": "但是",
            "grammar": "だけど＝だけれども，口语转折连词，但是"
        },
        {
            "original": "もしも何かあったら",
            "furigana": "もしも何（なに）かあったら",
            "translation": "如果发生了什么",
            "grammar": "もしも：万一、如果。あったら＝あった＋ら，如果发生"
        },
        {
            "original": "いつだって駆けつけるだろう",
            "furigana": "いつだって駆（か）けつけるだろう",
            "translation": "无论何时都会赶来的吧",
            "grammar": "いつだって＝いつでも，无论何时。駆けつける：赶到、奔赴。だろう：推量助动词，表示推测"
        },
        {
            "original": "何度傷つけば",
            "furigana": "何度（なんど）傷（きず）つけば",
            "translation": "要受多少次伤",
            "grammar": "何度～ば：几度...才..."
        },
        {
            "original": "月は欠けて行く",
            "furigana": "月（つき）は欠（か）けて行（ゆ）く",
            "translation": "月亮会逐渐缺去",
            "grammar": "欠けて：缺、残缺（动词て形）。行く：去、变得，这里表示渐进的过程"
        },
        {
            "original": "夜明けが 近づけば",
            "furigana": "夜明（よあ）けが 近（ちか）づけば",
            "translation": "黎明一旦临近",
            "grammar": "夜明け：黎明、天亮。近づけば＝近づく＋ば，如果接近的话"
        },
        {
            "original": "試練も静かに消える",
            "furigana": "試練（しれん）も静（しず）かに消（き）える",
            "translation": "试炼也会静静消失",
            "grammar": "試練：考验、试炼。も：提示助词，也。静かに：静静地（副词）"
        },
        {
            "original": "泥を払い",
            "furigana": "泥（どろ）を払（はら）い",
            "translation": "拂去泥土",
            "grammar": "払い：拂、掸（动词连用形）。表示中顿"
        },
        {
            "original": "立ち上がり",
            "furigana": "立（た）ち上（あ）がり",
            "translation": "站起来",
            "grammar": "立ち上がり：站起来（动词连用形），表示动作的接续"
        },
        {
            "original": "僕は姿勢を正す",
            "furigana": "僕（ぼく）は姿勢（しせい）を正（ただ）す",
            "translation": "我端正姿态",
            "grammar": "姿勢：姿势、态度。を：格助词，表示动作对象。正す：纠正、端正"
        },
        {
            "original": "つらいことが",
            "furigana": "つらいことが",
            "translation": "难过的事情",
            "grammar": "つらい：痛苦的、难过的（形容词）。が：格助词，表示主语"
        },
        {
            "original": "あった時には",
            "furigana": "あった時（とき）には",
            "translation": "发生的时候",
            "grammar": "あった：发生了（过去式）。時には：...的时候"
        },
        {
            "original": "瞼を静かに閉じて",
            "furigana": "瞼（まぶた）を静（しず）かに閉（と）じて",
            "translation": "静静地闭上眼睑",
            "grammar": "瞼：眼睑、眼皮。閉じて：关闭、闭上（动词て形）"
        },
        {
            "original": "今日の",
            "furigana": "今日（きょう）の",
            "translation": "今天的",
            "grammar": "今日：今天。の：连体修饰助词"
        },
        {
            "original": "大きな月を想って",
            "furigana": "大（おお）きな月（つき）を想（おも）って",
            "translation": "想着那轮大月亮",
            "grammar": "大きな：大的（连体词）。想って＝想う＋て，想着"
        },
        {
            "original": "迷ってる足下 照らそう",
            "furigana": "迷（まよ）ってる足下（あしもと） 照（て）らそう",
            "translation": "照亮迷茫的脚步",
            "grammar": "迷ってる＝迷っている，正在迷茫。照らそう＝照らす＋よう，让我们照亮吧（意志形）"
        },
        {
            "original": "自分に嘘つけば",
            "furigana": "自分（じぶん）に嘘（うそ）つけば",
            "translation": "如果对自己说谎",
            "grammar": "に：格助词，表示对象。嘘つけば＝嘘をつく＋ば，如果撒谎的话"
        },
        {
            "original": "自分を失うよ",
            "furigana": "自分（じぶん）を失（うしな）うよ",
            "translation": "就会失去自己哟",
            "grammar": "を：格助词，表示动作对象。失う：失去。よ：句末助词"
        },
        {
            "original": "月に雲がかかっても",
            "furigana": "月（つき）に雲（くも）がかかっても",
            "translation": "即使月亮被云遮住",
            "grammar": "に：格助词，表示动作涉及的对象。かかっても＝かかる＋ても，即使挂着/即使遮住"
        },
        {
            "original": "信じてるその道を進め!",
            "furigana": "信（しん）じてるその道（みち）を進（すす）め!",
            "translation": "相信那条道路前进吧！",
            "grammar": "信じてる＝信じている，相信着。進め：前进吧（命令形）"
        },
        {
            "original": "何度 傷つけば",
            "furigana": "何度（なんど） 傷（きず）つけば",
            "translation": "要受多少次伤",
            "grammar": "何度～ば：几度...才..."
        },
        {
            "original": "痛みを忘れる？",
            "furigana": "痛（いた）みを忘（わす）れる？",
            "translation": "才能忘记痛苦吗？",
            "grammar": "を：格助词。忘れる：忘记"
        },
        {
            "original": "赤い血を流せば",
            "furigana": "赤（あか）い血（ち）を流（なが）せば",
            "translation": "如果流下鲜红的血",
            "grammar": "流せば＝流す＋れば，如果流下"
        },
        {
            "original": "命を思い出すさ",
            "furigana": "命（いのち）を思（おも）い出（だ）すさ",
            "translation": "就会想起生命的意义啊",
            "grammar": "思い出す：想起。さ：句末助词，强调"
        },
        {
            "original": "道に倒れ",
            "furigana": "道（みち）に倒（たお）れ",
            "translation": "倒在路旁",
            "grammar": "に：表示地点。倒れ：倒下"
        },
        {
            "original": "大の字に",
            "furigana": "大（だい）の字（じ）に",
            "translation": "大字型地",
            "grammar": "大の字に：四仰八叉地"
        },
        {
            "original": "空を見上げて思う",
            "furigana": "空（そら）を望（み）上げて思（おも）う",
            "translation": "仰望着天空思索",
            "grammar": "見上げて：仰望。思う：想、思索"
        },
        {
            "original": "真の強さとは",
            "furigana": "真（しん）の強（つよ）さとは",
            "translation": "真正的强大是",
            "grammar": "強さ：强度、强大程度（名词）。とは：表示定义"
        },
        {
            "original": "夢を見る者",
            "furigana": "夢（ゆめ）を見（み）る者（もの）",
            "translation": "追梦之人",
            "grammar": "夢を見る：做梦、追梦。者：人、...的人"
        },
        {
            "original": "愛を信じる者",
            "furigana": "愛（あい）を信（しん）じる者（もの）",
            "translation": "相信爱之人",
            "grammar": "愛を信じる：相信爱。者：人"
        }
    ]
}

# 写入结果
task = load_pending_task()
write_result_to_file(json.dumps(result_json, ensure_ascii=False), task)
print("✅ 分析结果已写入 analysis_result.json")
print(f"✅ 共 {len(result_json['result'])} 句歌词分析完成")
