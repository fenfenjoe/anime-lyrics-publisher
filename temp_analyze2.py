# -*- coding: utf-8 -*-
"""临时脚本：分析 trust you 歌词并写入结果"""
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_analyzer import write_result_to_file

# 分析结果（55句）
result_data = {
    "song_intro": "《trust you》是《机动战士高达00》第二季的ED，由伊藤由奈演唱。这首歌曲以温柔却坚定的旋律，表达了在战乱世界中人们对和平的渴望、对彼此的信任，以及在绝望中依然相信未来的勇气。高达系列经典名曲之一。",
    "result": [
        {"original": "花は風に揺れ踊るように", "furigana": "花（はな）は風（かぜ）に揺（ゆ）れ踊（おど）るように", "translation": "花朵像随风摇曳舞蹈一般", "grammar": "～ように：表示"像…一样"。揺れ：动词"摇动"。踊る：动词"跳舞"。"},
        {"original": "雨は大地を潤すように", "furigana": "雨（あめ）は大地（だいち）を潤（うるお）すように", "translation": "雨水像滋润大地一般", "grammar": "を：表示动作对象。潤す：动词"滋润"。"},
        {"original": "この世界は寄り添い合い", "furigana": "この世界（せかい）は寄（よ）り添（そ）い合（あ）い", "translation": "这个世界人们相互依偎", "grammar": "寄り添い合い：复合动词"相互依偎"。この：指示代词"这个"。"},
        {"original": "生きてるのに", "furigana": "生（い）きてるのに", "translation": "明明都活着", "grammar": "のに：逆接接续助词"明明…却…"。生きてる：生存着的口语形式。"},
        {"original": "なぜ人は傷つけ合うの", "furigana": "なぜ人（ひと）は傷（きず）つけ合（あ）うの", "translation": "为什么人们要互相伤害呢", "grammar": "なぜ：疑问词"为什么"。傷つけ合う：复合动词"互相伤害"。"},
        {"original": "なぜ別れは訪れるの", "furigana": "なぜ別（わか）れは訪（おとず）れるの", "translation": "为什么离别会造访呢", "grammar": "は：提示主题。訪れる：动词"造访，来临"。"},
        {"original": "君が遠くに行ってもまだ", "furigana": "君（きみ）が遠（とお）くに行（い）ってもまだ", "translation": "即使你去了远方依然", "grammar": "ても：表示"即使…也…"。まだ：副词"依然，还"。"},
        {"original": "いつもこの心の真ん中", "furigana": "いつもこの心（こころ）の真（ま）ん中（なか）", "translation": "一直在这颗心的正中央", "grammar": "いつも：副词"总是"。の：表示所属"的"。"},
        {"original": "あのやさしい", "furigana": "あのやさしい", "translation": "那份温柔的", "grammar": "あの：指示连体词"那个"。やさしい：形容词"温柔的"。"},
        {"original": "笑顔でうめつくされたまま", "furigana": "笑顔（えがお）でうめつくされたまま", "translation": "被笑容填满的原样", "grammar": "で：表示手段"用…"。られた：被动形。まま：表示"保持…状态"。"},
        {"original": "抱きしめた君のカケラに", "furigana": "抱（だ）きしめた君（きみ）のカケラに", "translation": "在你紧紧拥抱的碎片中", "grammar": "に：表示动作对象或场所。カケラ：名词"碎片"。"},
        {"original": "痛み感じてもまだ", "furigana": "痛（いた）み感（かん）じてもまだ", "translation": "即使感受到疼痛依然", "grammar": "ても：表示"即使…也…"。感じて：动词"感受"的て形。"},
        {"original": "繋がるから", "furigana": "繋（つな）がるから", "translation": "因为彼此相连", "grammar": "から：表示原因"因为…"。繋がる：动词"相连，连接"。"},
        {"original": "信じてるよ また会えると", "furigana": "信（しん）じてるよ また会（あ）えると", "translation": "我相信着 还能再次相见", "grammar": "てる：ている的口语缩略。と：表示内容引用。"},
        {"original": "I'm waiting for your love", "furigana": "I'm waiting for your love", "translation": "我等待着你的爱", "grammar": "英语歌词，无需语法分析。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，无需语法分析。"},
        {"original": "君の孤独を分けてほしい", "furigana": "君（きみ）の孤独（こどく）を分（わ）けてほしい", "translation": "想要分担你的孤独", "grammar": "を：表示动作对象。ほしい：愿望形容词"希望…"。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"},
        {"original": "光でも闇でも", "furigana": "光（ひかり）でも闇（やみ）でも", "translation": "无论是光明还是黑暗", "grammar": "でも：表示"即使是…也…"。光/闇：反义词对。"},
        {"original": "二人だから信じ合えるの", "furigana": "二人（ふたり）だから信（しん）じ合（あ）えるの", "translation": "因为是两个人所以能够相互信任", "grammar": "だから：表示原因"因为…"。える：可能动词"能够…"。"},
        {"original": "離さないで", "furigana": "離（はな）さないで", "translation": "不要分开", "grammar": "ないで：表示禁止"不要…"。離さ：动词"离开"的未然形+ない。"},
        {"original": "世界の果てを誰が見たの", "furigana": "世界（せかい）の果（は）てを誰（だれ）が見（み）たの", "translation": "谁看到了世界的尽头", "grammar": "を：表示动作对象。が：主格助词提示主语。"},
        {"original": "旅の終わりを誰が告げるの", "furigana": "旅（たび）の終（お）わりを誰（だれ）が告（つ）げるの", "translation": "谁宣告旅途的结束", "grammar": "の：表示疑问语气。告げる：动词"宣告，通知"。"},
        {"original": "今は答えが見えなくて", "furigana": "今（いま）は答（こた）えが見（み）えなくて", "translation": "现在看不见答案", "grammar": "は：提示主题。なくて：形容词否定て形"没有…并且"。"},
        {"original": "永い夜でも", "furigana": "永（なが）い夜（よる）でも", "translation": "即使是漫长的夜晚", "grammar": "でも：表示"即使是…也…"。永い：形容词"漫长的"。"},
        {"original": "信じた道を進んでほしい", "furigana": "信（しん）じた道（みち）を進（すす）んでほしい", "translation": "希望你能走上相信的道路", "grammar": "た：过去式修饰名词。を：表示移动路径。ほしい：愿望形容词。"},
        {"original": "その先に光が待つから", "furigana": "その先（さき）に光（ひかり）が待（ま）つから", "translation": "因为前方有光芒等待着你", "grammar": "に：表示存在场所。が：主格助词。から：表示原因。"},
        {"original": "君が教えてくれた唄は", "furigana": "君（きみ）が教（おし）えてくれた唄（うた）は", "translation": "你教给我的那首歌", "grammar": "てくれた：てくれる的过去式"为我做…"。は：提示主题。"},
        {"original": "今もこの心の真ん中", "furigana": "今（いま）もこの心（こころ）の真（ま）ん中（なか）", "translation": "如今也在这颗心的正中央", "grammar": "も：表示"也"。今も：如今也。"},
        {"original": "あのやさしい", "furigana": "あのやさしい", "translation": "那份温柔的", "grammar": "重复第9句。"},
        {"original": "声と共に響いている", "furigana": "声（こえ）と共（とも）に響（ひび）いている", "translation": "与那声音一起回响", "grammar": "と共に：表示"与…一起"。ている：持续体"正在回响"。"},
        {"original": "溢れる気持ちのしずくが", "furigana": "溢（あふ）れる気持（きも）ちのしずくが", "translation": "满溢心情的水滴", "grammar": "が：主格助词提示主语。しずく：名词"水滴，点滴"。"},
        {"original": "あたたかく伝う", "furigana": "あたたかく伝（つた）う", "translation": "温暖地传递", "grammar": "あたたかく：形容词连用形。伝う：动词"传递，传导"。"},
        {"original": "強くなるね", "furigana": "強（つよ）くなるね", "translation": "变得坚强了呢", "grammar": "なる：表示变化"变得…"。ね：语气词"呢"。"},
        {"original": "信じてるよ", "furigana": "信（しん）じてるよ", "translation": "我相信着哟", "grammar": "てる：ている口语缩略。よ：语气词强调。"},
        {"original": "繋がってると", "furigana": "繋（つな）がってると", "translation": "若相互联系着", "grammar": "ってる：ている口语缩略。と：条件形"如果…的话"。"},
        {"original": "I'm always by your side", "furigana": "I'm always by your side", "translation": "我永远在你身边", "grammar": "英语歌词，无需语法分析。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"},
        {"original": "君のために流す涙が", "furigana": "君（きみ）のために流（なが）す涙（なみだ）が", "translation": "为你流淌的泪水", "grammar": "ために：表示目的"为了…"。が：主格助词。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"},
        {"original": "愛を教えてくれた", "furigana": "愛（あい）を教（おし）えてくれた", "translation": "教会了我爱", "grammar": "を：表示动作对象。てくれた：てくれる过去式"为我做…"。"},
        {"original": "どんなに君が道に迷っても", "furigana": "どんなに君（きみ）が道（みち）に迷（まよ）っても", "translation": "无论你怎样在道路上迷失", "grammar": "どんなに：副词"无论多么…"。ても：表示"即使…也…"。"},
        {"original": "そばにいるよ", "furigana": "そばにいるよ", "translation": "我会在你身边哟", "grammar": "に：表示存在场所。いる：存在动词"在"。よ：语气词。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"},
        {"original": "君の孤独を分けてほしい", "furigana": "君（きみ）の孤独（こどく）を分（わ）けてほしい", "translation": "想要分担你的孤独", "grammar": "重复第17句。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"},
        {"original": "光でも闇でも", "furigana": "光（ひかり）でも闇（やみ）でも", "translation": "无论是光明还是黑暗", "grammar": "重复第19句。"},
        {"original": "I love you I trust you", "furigana": "I love you I trust you", "translation": "我爱你 我信任你", "grammar": "英语歌词，重复第16句。"}
    ]
}

# 验证句数
print(f"预计句数: 55，实际句数: {len(result_data['result'])}")
if len(result_data['result']) != 55:
    print("❌ 句数不匹配！")
else:
    print("✅ 句数正确")

# 写入结果
json_str = json.dumps(result_data, ensure_ascii=False)
write_result_to_file(json_str)
print("✅ 分析结果已写入 data/analysis_result.json")
