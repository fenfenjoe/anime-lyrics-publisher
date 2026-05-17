import sys, json
sys.path.insert(0, r'E:\workspace\workbuddy\anime-lyrics-publisher')
from ai_analyzer import write_result_to_file

result_json = {
  "song_intro": "《自由の翼》是《进击的巨人》第一季最后一首ED，由Linked Horizon演唱，日德双语交织，激昂澎湃！每次听到那句[背中には自由の翼]我都鸡皮疙瘩——翅膀不是装饰，是誓死守护的信念。这首曲子把调查兵团那股视死如归的气魄诠释得淋漓尽致，强烈推荐！",
  "result": [
    {
      "original": "O mein freund",
      "furigana": "O mein freund",
      "translation": "哦，我的朋友",
      "grammar": "德语呼语句。mein 为德语第一人称所有格（我的），freund 为名词（朋友）。"
    },
    {
      "original": "Jetzt hier ist ein sieg",
      "furigana": "Jetzt hier ist ein sieg",
      "translation": "此刻此地，这是一场胜利",
      "grammar": "德语陈述句。jetzt（现在）、hier（这里）为副词，sieg 为名词（胜利），ein 为不定冠词。"
    },
    {
      "original": "Dies ist der erste gloria",
      "furigana": "Dies ist der erste gloria",
      "translation": "这是首次的荣光",
      "grammar": "德语陈述句。dies（这）为指示代词，erste（第一、首次）为序数词形容词，gloria（荣光/荣耀）为名词。"
    },
    {
      "original": "O mein freund",
      "furigana": "O mein freund",
      "translation": "哦，我的朋友",
      "grammar": "与第1句相同，德语呼语重复，强调情感共鸣。"
    },
    {
      "original": "Feiern wir diesen sieg für den nächsten Kampf",
      "furigana": "Feiern wir diesen sieg für den nächsten Kampf",
      "translation": "让我们为下一场战斗庆祝这场胜利",
      "grammar": "德语祈使句式（wir+动词原形倒装）。feiern（庆祝），diesen（这场），für（介词，为了），Kampf（战斗）。"
    },
    {
      "original": "「無意味な死であった」",
      "furigana": "「無意味（むいみ）な死（し）であった」",
      "translation": "「那是毫无意义的死亡」",
      "grammar": "①「無意味な」：ナ形容詞修饰名词「死」；②「であった」：断定助動詞「だ」的連用形「で」+「あった」（過去形），文语色彩。"
    },
    {
      "original": "と言わせない",
      "furigana": "と言（い）わせない",
      "translation": "不让人说出口",
      "grammar": "①「と」：引用助词，引导前句内容；②「言わせない」：言う（五段）→使役形「言わせる」→否定「言わせない」，表示不让某人说。"
    },
    {
      "original": "最後の一矢になるまで",
      "furigana": "最後（さいご）の一矢（いっし）になるまで",
      "translation": "直到成为最后一支箭",
      "grammar": "①「の」：格助词连接修饰；②「になる」：变化表达，变成某状态；③「まで」：限定助词，表示到……为止。"
    },
    {
      "original": "Der feind ist grausam wir bringen",
      "furigana": "Der feind ist grausam wir bringen",
      "translation": "敌人残暴，我们出击",
      "grammar": "德语。feind（敌人），grausam（残忍的），bringen（出击），两个并列小句构成对比。"
    },
    {
      "original": "Der feind ist riesig wir springen",
      "furigana": "Der feind ist riesig wir springen",
      "translation": "敌人巨大，我们跃起",
      "grammar": "德语。riesig（巨大的），springen（跳跃），与上句结构平行，形成排比。"
    },
    {
      "original": "両手には鋼刃",
      "furigana": "両手（りょうて）には鋼刃（こうじん）",
      "translation": "双手持钢刃",
      "grammar": "①「には」：格助词「に」+「は」，表示在某处有；②省略述語的体言止，名词结句，增强节奏感。"
    },
    {
      "original": "唄うのは凱歌",
      "furigana": "唄（うた）うのは凱歌（がいか）",
      "translation": "吟唱的是凯歌",
      "grammar": "①「唄うの」：動詞+「の」名词化；②「は」：主题助词；③体言止，以名词凱歌结句。"
    },
    {
      "original": "背中には自由の翼",
      "furigana": "背中（せなか）には自由（じゆう）の翼（つばさ）",
      "translation": "背上是自由的羽翼",
      "grammar": "①「には」：「に」（存在场所）+「は」（主题标记）；②「の」：格助词连接自由与翼；③体言止。"
    },
    {
      "original": "握り締めた決意を左胸に",
      "furigana": "握（にぎ）り締（し）めた決意（けつい）を左胸（ひだりむね）に",
      "translation": "将紧握的决意置于左胸",
      "grammar": "①「握り締めた」：複合動詞連体形修饰決意；②「を」：格助词表动作对象；③「に」：格助词表方向/归着点。"
    },
    {
      "original": "斬り裂くのは愚行の螺旋",
      "furigana": "斬（き）り裂（さ）くのは愚行（ぐこう）の螺旋（らせん）",
      "translation": "斩断的是愚行的漩涡",
      "grammar": "①「斬り裂くの」：複合動詞名词化；②「は」：主题助词；③「の」格助词连接修饰。体言止结构。"
    },
    {
      "original": "蒼穹を舞う",
      "furigana": "蒼穹（そうきゅう）を舞（ま）う",
      "translation": "在苍穹中翱翔",
      "grammar": "①「を」：格助词，用于移動動詞前表示经过的空间；②「舞う」：五段動詞，翩飞之意。"
    },
    {
      "original": "自由の翼",
      "furigana": "自由（じゆう）の翼（つばさ）",
      "translation": "自由的羽翼",
      "grammar": "「の」：格助词表所属/修饰。体言止短语，本曲标题的核心意象。"
    },
    {
      "original": "鳥は飛ぶ為に",
      "furigana": "鳥（とり）は飛（と）ぶ為（ため）に",
      "translation": "鸟儿是为了飞翔",
      "grammar": "①「は」：主题助词；②「飛ぶ為に」：動詞連体形+「為に」表目的（为了……）。"
    },
    {
      "original": "其の殻を破ってきた",
      "furigana": "其（そ）の殻（から）を破（やぶ）ってきた",
      "translation": "才打破了那层枷锁",
      "grammar": "①「其の」：指示连体词；②「を」：对象格助词；③「破ってきた」：て形+「きた」（補助），表从某状态变化而来延续至今。"
    },
    {
      "original": "無様に地を這う為じゃないだろ？",
      "furigana": "無様（ぶざま）に地（ち）を這（は）う為（ため）じゃないだろ？",
      "translation": "不是为了狼狈地匍匐于大地吧？",
      "grammar": "①「無様に」：ナ形容詞副詞形；②「為じゃない」：目的表达的否定；③「だろ？」：推量口语形，表反问。"
    },
    {
      "original": "お前の翼は何の為にある",
      "furigana": "お前（まえ）の翼（つばさ）は何（なん）の為（ため）にある",
      "translation": "你的翅膀，究竟为何而存在",
      "grammar": "①「お前の」：第二人称所有格；②「何の為に」：目的疑问形式；③「ある」：存在动词，用于非生命/抽象事物。"
    },
    {
      "original": "籠の中の空は狭過ぎるだろ？",
      "furigana": "籠（かご）の中（なか）の空（そら）は狭（せま）過（す）ぎるだろ？",
      "translation": "笼中的天空太狭小了吧？",
      "grammar": "①「の中の」：双重の表示里面的；②「狭過ぎる」：形容詞語幹+「過ぎる」，过于……；③「だろ？」：反问语气。"
    },
    {
      "original": "Die freiheit und der tod",
      "furigana": "Die freiheit und der tod",
      "translation": "自由与死亡",
      "grammar": "德语名词短语。freiheit（自由），tod（死亡），und（和），并列结构。"
    },
    {
      "original": "Die beiden sind zwilling",
      "furigana": "Die beiden sind zwilling",
      "translation": "两者乃双生之物",
      "grammar": "德语。beiden（两者），zwilling（双胞胎/双生），隐喻自由与死亡密不可分。"
    },
    {
      "original": "Die freiheit oder der tod",
      "furigana": "Die freiheit oder der tod",
      "translation": "不自由，毋宁死",
      "grammar": "德语选择句。oder（或者），与上句und（和）形成对比，由并列变为非此即彼。"
    },
    {
      "original": "Unser freund ist ein",
      "furigana": "Unser freund ist ein",
      "translation": "我们的朋友是一体的",
      "grammar": "德语。unser（我们的），freund（朋友），ein（一/同一），战友即命运共同体。"
    },
    {
      "original": "何の為に",
      "furigana": "何（なん）の為（ため）に",
      "translation": "为了什么",
      "grammar": "「何の為に」：疑问词+の+「為に」表目的疑问。单独成句，形成强调，是全曲哲学核心。"
    },
    {
      "original": "生まれて来たのかなんて",
      "furigana": "生（う）まれて来（き）たのかなんて",
      "translation": "究竟是为何降临于世",
      "grammar": "①「生まれて来た」：複合動詞，来到世界出生；②「のか」：内心独白疑问；③「なんて」：轻蔑/自嘲语气助词。"
    },
    {
      "original": "小難しい事は解らないけど",
      "furigana": "小難（こむずか）しい事（こと）は解（わ）からないけど",
      "translation": "那些复杂难懂的道理我不明白，但是",
      "grammar": "①「小難しい」：前缀「小」+難しい，略微复杂难懂的；②「は」：对比主题助词；③「けど」：逆接，口语形式。"
    },
    {
      "original": "例え其れが過ちだったとしても",
      "furigana": "例（たと）え其（そ）れが過（あやま）ちだったとしても",
      "translation": "就算那是个错误",
      "grammar": "①「例え～としても」：固定让步句式，即使……也……；②「過ちだった」：名词+だった（过去断定）。"
    },
    {
      "original": "何の為に生きているかは判る",
      "furigana": "何（なん）の為（ため）に生（い）きているかは判（わか）る",
      "translation": "为何而活着，这我清楚",
      "grammar": "①「生きているか」：現在進行形+「か」（疑問的名词化）；②「は」：主题提示；③「判る」：知晓，比分かる更正式。"
    },
    {
      "original": "其れは理屈じゃない",
      "furigana": "其（そ）れは理屈（りくつ）じゃない",
      "translation": "那不是什么道理逻辑",
      "grammar": "①「は」：主题助词；②「理屈じゃない」：名词+「じゃない」口语否定，强调超越理性的本能信念。"
    },
    {
      "original": "存在故の『自由』",
      "furigana": "存在（そんざい）故（ゆえ）の『自由（じゆう）』",
      "translation": "正因存在，才有『自由』",
      "grammar": "①「故の」：文语连体形，因……而来的；②体言止，哲学意味浓厚；③呼应我存在故我自由的理念。"
    },
    {
      "original": "Die Flügel der Freiheit",
      "furigana": "Die Flügel der Freiheit",
      "translation": "自由的羽翼",
      "grammar": "德语名词短语。Flügel（翅膀），der Freiheit（自由的，属格），即本曲标题的德语原名。"
    },
    {
      "original": "隠された真実は",
      "furigana": "隠（かく）された真実（しんじつ）は",
      "translation": "被隐藏的真相——",
      "grammar": "①「隠された」：受動連体形，被隐藏的；②「は」：主题助词，后省略述語，形成悬念。"
    },
    {
      "original": "衝撃の嚆矢だ",
      "furigana": "衝撃（しょうげき）の嚆矢（こうし）だ",
      "translation": "是震撼的第一箭",
      "grammar": "①「の」：格助词修饰嚆矢；②「嚆矢」：本义响箭，引申为开端先驱；③「だ」：断定助動詞结句。"
    },
    {
      "original": "鎖された其の深層と",
      "furigana": "鎖（とざ）された其（そ）の深層（しんそう）と",
      "translation": "那被封锁的深处，与",
      "grammar": "①「鎖された」：受動形，被封锁的；②「と」：并列助词，引出下一句结构。"
    },
    {
      "original": "表層に潜む巨人達",
      "furigana": "表層（ひょうそう）に潜（ひそ）む巨人（きょじん）達（たち）",
      "translation": "潜伏于表层的巨人们",
      "grammar": "①「に潜む」：格助词に+存在動詞，藏匿于某处；②「達」：复数接尾词。"
    },
    {
      "original": "崩れ然る固定観念",
      "furigana": "崩（くず）れ然（さ）る固定観念（こていかんねん）",
      "translation": "崩塌瓦解的固有观念",
      "grammar": "①「崩れ然る」：複合語，然る为文语形式如此地崩裂；②「固定観念」：四字熟语，固有成见。体言止。"
    },
    {
      "original": "迷いを抱きながら",
      "furigana": "迷（まよ）いを抱（いだ）きながら",
      "translation": "心怀迷茫，却",
      "grammar": "①「迷い」：動詞迷う的名詞形；②「を抱き」：格助词+連用形；③「ながら」：接続助詞，一边……一边……或让步。"
    },
    {
      "original": "其れでも尚",
      "furigana": "其（そ）れでも尚（なお）",
      "translation": "即便如此，依然",
      "grammar": "①「それでも」：逆接接続詞，即便如此；②「尚」：副词，仍然依然，叠加强调坚定意志。"
    },
    {
      "original": "『自由』へ進め",
      "furigana": "『自由（じゆう）』へ進（すす）め",
      "translation": "向着『自由』前进！",
      "grammar": "①「へ」：格助词表方向；②「進め」：五段動詞進む的命令形，语气强烈。"
    },
    {
      "original": "Rechter weg",
      "furigana": "Rechter weg",
      "translation": "右边的路",
      "grammar": "德语名词短语。rechter（右边的），weg（路），象征面临抉择。"
    },
    {
      "original": "Linker weg",
      "furigana": "Linker weg",
      "translation": "左边的路",
      "grammar": "德语。linker（左边的），与rechter weg对称，暗示前行路上的两难困境。"
    },
    {
      "original": "Na ein weg welcher ist",
      "furigana": "Na ein weg welcher ist",
      "translation": "那么，究竟是哪条路",
      "grammar": "德语疑问结构。na（那么），welcher（哪一个，疑问代词），在两条道路间的困惑追问。"
    },
    {
      "original": "Der feind",
      "furigana": "Der feind",
      "translation": "那是敌人",
      "grammar": "德语名词短语。feind（敌人），单独成句形成强调，与下句朋友构成对立。"
    },
    {
      "original": "Der freund",
      "furigana": "Der freund",
      "translation": "那是朋友",
      "grammar": "德语名词短语。freund（朋友），与feind呼应，暗示战场上敌我难辨的困境。"
    },
    {
      "original": "Mensch sie welche sind",
      "furigana": "Mensch sie welche sind",
      "translation": "他们究竟是怎样的人",
      "grammar": "德语。Mensch（人），sie（他们），welche（什么样的），sind（是），疑问倒装，追问人的本质。"
    },
    {
      "original": "両手には戦意",
      "furigana": "両手（りょうて）には戦意（せんい）",
      "translation": "双手持战意",
      "grammar": "呼应第11句両手には鋼刃，将钢刃升华为战意，精神意志强化。体言止，には同前。"
    },
    {
      "original": "唄うのは希望",
      "furigana": "唄（うた）うのは希望（きぼう）",
      "translation": "吟唱的是希望",
      "grammar": "呼应第12句唄うのは凱歌，将凯歌升华为希望，同构替换，意象递进。"
    },
    {
      "original": "背中には自由の地平線",
      "furigana": "背中（せなか）には自由（じゆう）の地平線（ちへいせん）",
      "translation": "背上是自由的地平线",
      "grammar": "呼应第13句背中には自由の翼，以地平线替换翅膀，视野从飞翔扩展为整片大地的自由。の格助词修饰。"
    },
    {
      "original": "世界を繋ぐ鎖を各々胸に",
      "furigana": "世界（せかい）を繋（つな）ぐ鎖（くさり）を各々（おのおの）胸（むね）に",
      "translation": "将连结世界的锁链，各自铭记于心",
      "grammar": "①「世界を繋ぐ」：動詞連体形修饰鎖；②「各々」：副词各自；③「胸に」：に表归着点。"
    },
    {
      "original": "奏でるのは可能性の背面",
      "furigana": "奏（かな）でるのは可能性（かのうせい）の背面（はいめん）",
      "translation": "演奏的是可能性的背面",
      "grammar": "①「奏でるの」：動詞連体形名词化；②「は」主题助词；③「可能性の背面」深邃意象，暗示无限可能性背后的另一面。体言止。"
    },
    {
      "original": "蒼穹を舞え",
      "furigana": "蒼穹（そうきゅう）を舞（ま）え",
      "translation": "在苍穹中翱翔吧！",
      "grammar": "呼应第16句蒼穹を舞う，舞え为命令形，语气由描述变为号令，情感爆发。を表移動空間。"
    },
    {
      "original": "自由の翼",
      "furigana": "自由（じゆう）の翼（つばさ）",
      "translation": "自由的羽翼",
      "grammar": "全曲最终落幅，の格助词连接。标题意象在结尾再度升腾，余韵悠长。"
    }
  ]
}

json_str = json.dumps(result_json, ensure_ascii=False, indent=2)
write_result_to_file(json_str)
