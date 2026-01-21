# 姒傚康璁捐鏂囨。 (Concept Design Document)

# 鑽夌
杩欐槸涓€涓潪甯告鐨勬蹇佃璁℃€濊矾銆傚紩鍏?Scoring (浠茶鑰? 鍜?Execution (鎵ц瀹? 鐨勬灦鏋勶紝瀹為檯涓婃槸灏嗛噺鍖栧洖娴嬬郴缁熶腑鐨?淇″彿鐢熸垚 (Signal Generation)銆佹姇璧勭粍鍚堟瀯寤?(Portfolio Construction) 鍜?浜ゆ槗鎵ц (Execution) 杩涜浜嗘洿楂樼骇鐨勮В鑰︺€?

鐩告瘮浜庣敓鎴愪竴寮犻潤鎬佺殑鈥滀簰鏂ヨ〃鈥濓紙杩欏湪鍥犲瓙鍙樺鏃朵細鍛堢幇鎸囨暟绾у鏉傚害鐖嗙偢锛屼笖闅句互缁存姢锛夛紝浣犵殑 Scoring/Execution 妯″紡鏇寸鍚堢幇浠ｉ噺鍖栫郴缁熺殑璁捐鍝插锛堝 QuantConnect 鎴?Zipline 鐨勬灦鏋勶級銆?

浠ヤ笅鎴戜负浣犺璁＄殑绯荤粺鏋舵瀯钃濆浘锛屽畾涔変簡瀹冧滑鍚勮嚜鐨勮亴璐ｅ拰鏁板閫昏緫銆?

鏍稿績鏋舵瀯锛歅lan, Symbol, Factor, Scoring, Execution
鍦ㄨ繖涓綋绯讳腑锛屾暟鎹祦鍚戝簲璇ユ槸锛?

Data\xrightarrowFactorSignal\xrightarrowScoringTarget Portfolio\xrightarrowExecutionOrders

1. Factor (鍥犲瓙/绛栫暐鍗曞厓) 鈥斺€?鈥滄劅鐭ヨ€呪€?
浣犳彁鍒扮殑 Factor 鍦ㄨ繖閲屼笉浠呬粎鏄暟瀛﹀洜瀛愶紙濡?PE, RSI锛夛紝鏇村簲璇ヨ瀹氫箟涓?Signal Generator (淇″彿鍙戠敓鍣?銆?

杈撳叆锛歋ymbol 鐨勫競鍦烘暟鎹紙OHLCV锛夈€佽储鍔℃暟鎹€?
杈撳嚭锛氫竴涓爣鍑嗗寲鐨勪俊鍙峰己搴?(Signal Strength) 鎴?寤鸿浠撲綅 (Raw Weight)銆?
鐗规€э細
鍥犲瓙涔嬮棿涓嶉渶瑕佺煡閬撳郊姝ょ殑瀛樺湪锛堣В鑰︼級銆?
Buy & Hold 鍙互琚涓轰竴涓壒娈婄殑鍥犲瓙锛氬畠濮嬬粓杈撳嚭 
1
.
0
1.0锛堟弧浠擄級鐨勪俊鍙枫€?
鍧囧€煎洖褰掑洜瀛?鍙兘杈撳嚭 
[
鈭?
]
[鈭?,1] 涔嬮棿鐨勬尝鍔ㄤ俊鍙枫€?
1. Scoring (浠茶鑰? 鈥斺€?鈥滃喅绛栧ぇ鑴戔€?
杩欐槸浣犵郴缁熺殑鏍稿績銆侫rbiter 涓嶇洿鎺ヤ氦鏄擄紝瀹冪殑鑱岃矗鏄В鍐冲啿绐佸拰鍒嗛厤鏉冮噸銆傚畠鍐冲畾浜嗏€滄鏃舵鍒伙紝鎴戜滑鐞嗘兂鐨勬寔浠撳簲璇ユ槸浠€涔堚€濄€?

鑱岃矗锛?

淇″彿鑱氬悎 (Aggregation)锛氭帴鏀舵墍鏈?Factor 鐨勮緭鍑恒€?
鍐茬獊瑙ｅ喅 (Conflict Resolution)锛氬綋 Factor A 鎯充拱锛孎actor B 鎯冲崠鏃讹紝Scoring 鍐冲畾鍚皝鐨勶紝鎴栬€呭彇鎶樹腑鍊笺€?
椋庨櫓鎺у埗 (Risk Constraints)锛氫緥濡傞檺鍒跺崟鍙偂绁ㄦ渶澶т粨浣嶄笉瓒呰繃 20%銆?
杈撳嚭锛氱洰鏍囨姇璧勭粍鍚?(Target Portfolio / Target Weights)銆?
瑙ｅ喅鈥滀簰鏂モ€濈殑閫昏緫锛?
涓嶉渶瑕佷簰鏂ヨ〃锛岃€屾槸閫氳繃鏉冮噸鍙犲姞鎴栦紭鍏堢骇鎺╃爜鏉ュ鐞嗐€?

鍦烘櫙涓句緥锛欱uy & Hold vs. 鎷╂椂鍥犲瓙
鍋囪浣犳湁涓€涓熀鍑嗙瓥鐣ワ紙Buy & Hold锛夊拰涓€涓寮虹瓥鐣ワ紙MACD锛夈€?

Factor A (Buy & Hold): 杈撳嚭 
S
0
S
鈥婣
鈥嬧€?=1.0 (濮嬬粓寤鸿鎸佹湁)銆?
Factor B (MACD Sell): 杈撳嚭 
S
B
=
鈭?
鈥婤
鈥嬧€?=鈭?.5 (寤鸿鍑忎粨)銆?
Scoring 鐨勯€昏緫锛?
W
5
1.0+(鈭?.5)=0.5锛堝崐浠擄級銆?
缁撹锛氬啿绐侀€氳繃鏁板鍔犳潈鑷劧娑堣В浜嗭紝鑰屼笉鏄‖鎬х殑鈥滀簰鏂モ€濄€?
1. Execution (鎵ц瀹? 鈥斺€?鈥滆鍔ㄦ墜鑴氣€?
Execution 璐熻矗灏?Scoring 鐨勨€滅悊鎯斥€濊浆鍖栦负鈥滅幇瀹炩€濄€傚畠澶勭悊甯傚満鎽╂摝鍜屽疄闄呬氦鏄撹鍒欍€?

杈撳叆锛欰rbiter 缁欏嚭鐨?Target Portfolio锛堜緥濡傦細鎸佹湁鑼呭彴 20%锛屾寔鏈夊畞寰锋椂浠?30%锛夈€?
鑱岃矗锛?
鐘舵€佸姣旓細姣旇緝 Current Portfolio (褰撳墠鎸佷粨) 鍜?Target Portfolio銆?
鐢熸垚璁㈠崟 (Order Generation)锛氳绠楀樊棰濓紙Diff锛夈€?

鈥?
鈥?Target Weight鈭扖urrent Weight)脳Total Equity
鈥嬧€?

浜ゆ槗闄愬埗 (Constraints)锛?
A鑲¤鍒欙細蹇呴』鏄?100 鑲＄殑鏁存暟鍊?(Round down to lot size)銆?
T+1 妫€鏌ワ細鏄ㄥぉ鐨勪拱鍏ヤ粖澶╂墠鑳藉崠銆?
娑ㄨ穼鍋滄鏌ワ細濡傛灉娑ㄥ仠锛屾棤娉曚拱鍏ワ紱璺屽仠锛屾棤娉曞崠鍑恒€?
鐜伴噾妫€鏌ワ細鏄惁鏈夎冻澶熺殑 Cash銆?
杈撳嚭锛氭渶缁堢殑 Buy/Sell 浜ゆ槗鎸囦护鍒楄〃銆?
鏁板妯″瀷璁捐
涓轰簡璁╃郴缁熸敮鎸佺嚎鎬?闈炵嚎鎬т互鍙婂鏉傜殑鍙犲姞锛屽缓璁噰鐢ㄤ互涓嬫暟瀛︽ā鍨嬶細

1. 鍥犲瓙灞?(Factor Layer)
姣忎釜 Factor 
f
鈥嬧€? 閽堝鏌愪釜 Symbol 
s
s 鍦ㄦ椂闂?
t
t 杈撳嚭涓€涓俊鍙?
v
i
,
鈥媔,s,t
鈥嬧€?銆?
涓轰簡鏍囧噯鍖栵紝寤鸿灏嗘墍鏈夊洜瀛愮殑杈撳嚭褰掍竴鍖栧埌 
[
鈭?
1
[鈭?,1] 鎴?
[
0
,
[0,1] 鍖洪棿銆?

1. 浠茶灞?(Scoring Layer)
Scoring 浣跨敤涓€涓嚱鏁?
A
A 鏉ヨ绠楃洰鏍囨潈閲?
W

鍏朵腑 
螛
螛 鏄?Scoring 鐨勯厤缃弬鏁般€?

妯″紡 A锛氱嚎鎬у姞鏉?(Linear Combination)
閫傚悎澶氬洜瀛愬彔鍔犮€?

W
s
,
#+ 姒傚康璁捐鏂囨。 (Concept Design Document)

**鐗堟湰**: 2.0  
**鏃ユ湡**: 2026-01-06  
**閫傜敤鑼冨洿**: A 鑲′腑闀跨嚎澶氭爣鐨勫洖娴嬩笌妯℃嫙浜ゆ槗寮曟搸  
**闃呰瀵硅薄**: 閲忓寲宸ョ▼甯?/ 鐮旂┒鍛?/ QA / 杩愮淮

---

## 1. 鐩爣涓庤寖鍥?

- 寤虹珛涓€濂楄В鑰︺€佸彲娴嬭瘯銆佸彲鎵╁睍鐨勫洖娴?妯℃嫙浜ゆ槗鍐呮牳锛岃鐩栨暟鎹啋淇″彿鈫掑喅绛栤啋鎵ц鈫掓竻绠椻啋鎶ュ憡鐨勫叏閾捐矾銆? 
- 閽堝 A 鑲＄壒鎬э紙T+1銆?00 鑲℃暣鎵嬨€佹定璺屽仠銆佸垎绾㈤€佽浆銆佸嵃鑺辩◣锛夋彁渚涗竴绛夊叕姘戠殑宸ョ▼灏佽銆? 
- 棰勭暀鏈哄櫒瀛︿範涓庡己鍖栧涔犵殑婕旇繘鎺ュ彛锛屼繚鎸佽緭鍏?杈撳嚭濂戠害绋冲畾銆? 
- 杈撳嚭浜や粯鐗╋細鏍稿績妯″潡璁捐銆佹暟鎹绾︺€佸叧閿祦绋嬨€佺害鏉熶笌娴嬭瘯瑕佹眰銆?

闈炵洰鏍囷細鎾悎寮曟搸楂橀缁嗙矑搴︽ā鎷熴€佷氦鏄撻€氶亾瀹炵洏鎺ュ叆銆佽秴鏃ュ唴锛堝垎閽熺骇锛夊欢杩熷缓妯°€?

---

## 2. 鍏抽敭姒傚康涓庤鑹?

- Plan锛氫竴娆″洖娴?妯℃嫙浠诲姟鐨勯厤缃泦鍚堬紙瀹囧畽銆佸洜瀛愬垪琛ㄣ€佷徊瑁侀€昏緫銆佹墽琛屼笌鎴愭湰妯″瀷銆佽皟搴﹀懆鏈燂級銆? 
- Nexus/Universe锛氭暟鎹叆鍙ｄ笌鍙氦鏄撴爣鐨勭瓫閫夊眰銆? 
- Factor/Factor锛氫俊鍙峰彂鐢熷櫒锛岃緭鍑烘爣鍑嗗寲寮哄害鎴栧缓璁潈閲嶃€? 
- Scoring锛氫俊鍙疯仛鍚堜笌鐩爣鏉冮噸鍐崇瓥灞傘€? 
- Execution锛氬皢鐩爣鏉冮噸杞寲涓哄彲涓嬪崟鐨勮鍗曡崏妗堬紝璐熻矗 A 鑲＄害鏉熸牎楠屻€? 
- Broker/Account锛氭垚浜ゆ挳鍚堜笌璁拌处锛岀淮鎶よ祫閲戜笌鎸佷粨鐘舵€併€? 
- Scheduler锛氳皟浠撹妭濂忎笌闃堝€兼帶鍒讹紙鍙唴宓屽湪 Scoring锛屼篃鍙嫭绔嬶級銆? 
- Analyzer/Reporter锛氱哗鏁堟寚鏍囦笌鏃ュ織杈撳嚭銆? 
- CostModel/Slippage锛氭墜缁垂銆佸嵃鑺辩◣銆佹粦鐐逛笌鏈€浣庤垂鐢ㄨ鍒欓泦鍚堛€?

---

## 3. 鏁翠綋鏋舵瀯涓庢暟鎹祦

鏁版嵁娴侊細

1. Nexus锛氭媺鍙栧苟娓呮礂褰撴棩鏁版嵁锛涚敓鎴?`ActiveUniverse`锛堝彲浜ゆ槗鏍囩殑鍒楄〃锛夈€? 
2. Factors锛氬 `ActiveUniverse` 骞惰璁＄畻 `SignalFrame`銆? 
3. Scoring锛氭帴鏀?`SignalFrame` + `AccountState`锛岃緭鍑?`TargetPortfolio`銆? 
4. Execution锛氬姣?`TargetPortfolio` 涓庡綋鍓嶆寔浠擄紝鐢熸垚婊¤冻绾︽潫鐨?`Orders`銆? 
5. Broker/Account锛氬熀浜庢挳鍚堜环鏍间笌鎴愭湰妯″瀷鐢熸垚 `Fills`锛屾洿鏂?`AccountState`銆? 
6. Analyzer锛氳褰曞綋鏃?`Nav`, `Trades`, `Positions`锛屾洿鏂版寚鏍囥€? 
7. Loop锛氭帹杩涘埌涓嬩竴浜ゆ槗鏃ワ紝鐩磋嚦缁撴潫銆?

閫昏緫鍒嗗眰锛?
- 璁＄畻灞傦紙Factors, Scoring锛変笉鎰熺煡甯傚満鎽╂摝銆? 
- 绾︽潫灞傦紙Execution, Broker锛夋敹鍙ｆ墍鏈?A 鑲＄壒鏈夎鍒欎笌鎴愭湰銆? 
- 鐘舵€佸眰锛圓ccount锛夋槸鍞竴鐨勮祫閲?鎸佷粨鐪熺浉婧愩€? 
- 瑙傛祴灞傦紙Analyzer锛夊彧璇荤姸鎬佷笌鎴愪氦銆?

---

## 4. 鏍稿績妯″潡璁捐

### 4.1 Nexus / Universe
- 杈撳叆锛氬師濮嬭鎯呫€佽储鍔°€佹棩鍘嗐€佸仠鐗屻€佹垚鍒嗗彉鏇淬€佸垎绾㈤€佽浆琛ㄣ€? 
- 杈撳嚭锛歚ActiveUniverse`锛堝彲浜ゆ槗鏍囩殑鍒楄〃锛夈€佸榻愪笖缂哄け鍊煎鐞嗗悗鐨?`DataFrame`/tensor銆? 
- 瑙勫垯锛氬墧闄?ST/PT銆佷笂甯傚皬浜?N 澶┿€佸仠鐗屻€侀€€甯傦紱鍙厤缃垚鍒嗭紙濡?HS300锛夈€? 
- 宸ョ▼瑕佺偣锛?
  - 鏁版嵁瀵归綈涓庡墠鍚戝～鍏呯瓥鐣ユ槑纭褰曪紱
  - 浜ゆ槗鏃ュ巻缁熶竴鍏ュ彛锛?
  - 鐢熷瓨鍋忓樊闃叉姢锛堝巻鍙叉垚鍒嗕笌閫€甯傝〃锛夈€?

### 4.2 Factors (Factors)
- 杈撳叆锛歚ActiveUniverse` 鏁版嵁鍒囩墖銆? 
- 杈撳嚭锛歚SignalFrame`锛屽舰濡?`(time, symbol) -> signal 鈭?[-1,1] 鎴?[0,1]`锛屽厑璁?`NaN` 琛ㄧず鏃犱俊鍙枫€? 
- 璁捐鍘熷垯锛?
  - 瀹屽叏鏃犲壇浣滅敤锛?
  - 涓嶆劅鐭ヨ祫閲戜笌浠撲綅锛?
  - 闇€澹版槑鎵€闇€鏁版嵁鍒椾笌绐楀彛澶у皬锛屼究浜庤皟搴﹀櫒鍋氱紦瀛樹笌瑁佸壀銆? 
- 绀轰緥锛氬姩閲忋€佸潎绾裤€佸绌鸿瘎鍒嗐€侀闄╁紑鍏筹紙鐔旀柇淇″彿锛夈€?

### 4.3 Scoring
- 杈撳叆锛歚SignalFrame`, `AccountState`, 鍙€?`RiskSignals`銆? 
- 杈撳嚭锛歚TargetPortfolio`锛堝悇 symbol 鐩爣鏉冮噸 + 鐜伴噾鏉冮噸锛夈€? 
- 甯歌绛栫暐锛?
  - 绾挎€у姞鏉冿細$w_s = \sum_i \alpha_i \cdot signal_{i,s}$銆? 
  - 闂ㄦ帶/鎺╃爜锛歚base_weight * (1 - risk_mask)`锛涢噸澶ч闄╀俊鍙峰彲涓€绁ㄥ惁鍐炽€? 
  - 闃叉姈锛氳嫢 `|target - current| < threshold` 鍒欎繚鎸佷笉鍔ㄣ€? 
- 宸ョ▼瑕佺偣锛?
  - 杈撳嚭鏉冮噸闇€褰掍竴鍖栧苟绾︽潫鍦?$[0,1]$锛?
  - 鍏佽鐜伴噾鏉冮噸锛?
  - 淇濇寔鎺ュ彛绋冲畾锛屽唴閮ㄥ彲鏇挎崲涓?ML/RL銆?

### 4.4 Scheduler锛堝彲閫夌嫭绔嬶級
- 鍔熻兘锛氭帶鍒惰皟浠撻鐜囦笌瑙﹀彂鏉′欢銆? 
- 绀轰緥锛氭瘡鏈堢涓€涓氦鏄撴棩閲嶅钩琛★紱鎴栧綋缁勫悎鍙樺姩瓒?5% 鏃惰Е鍙戙€? 
- 鑻ヤ笉鐙珛锛屽垯鍦?Scoring 鍐呴儴瀹炵幇闃叉姈閫昏緫銆?

### 4.5 Execution
- 杈撳叆锛歚TargetPortfolio`, `AccountState`, 褰撴棩鐩樺彛浠锋牸/闄愬埗銆? 
- 杈撳嚭锛歚Orders`锛堟弧瓒虫暣鎵嬨€乀+1銆佹定璺屽仠銆佽祫閲戠害鏉熺殑涔板崠鍒楄〃锛夈€? 
- 绾︽潫瑙勫垯锛?
  - Lot size锛氭暟閲忓悜涓嬪彇鏁村埌 100 鑲★紱
  - T+1锛氬崠鍑洪渶妫€鏌?`sellable_shares`锛?
  - 娑ㄨ穼鍋滐細娑ㄥ仠涓嶄拱锛岃穼鍋滀笉鍗栵紙鍙厤缃瓥鐣ヤ緥澶栵級锛?
  - 璧勯噾锛氫拱鍏ラ噾棰?+ 璐圭敤 鈮?鍙敤鐜伴噾锛?
  - 鎴愪氦浠凤細榛樿鏀剁洏浠锋垨 VWAP锛屽彲閰嶇疆婊戠偣鍑芥暟銆? 
- 璁㈠崟褰㈡€侊細鏀寔 `MARKET`/`LIMIT`锛涚揣鎬ュ害瀛楁鐢ㄤ簬婊戠偣妯″瀷銆?

### 4.6 Broker / Account
- 杈撳叆锛歚Orders`, 褰撴棩浠锋牸銆佸垎绾㈤€佽浆浜嬩欢銆佹垚鏈ā鍨嬨€? 
- 杈撳嚭锛歚Fills`, 鏇存柊鍚庣殑 `AccountState`銆? 
- 鑱岃矗锛?
  - 鎾悎锛氭牴鎹环鏍兼ā鍨嬬粰鍑烘垚浜ら噺涓庢垚浜や环锛?
  - 璐圭敤锛氫剑閲戙€佸嵃鑺辩◣锛堝崠鍑烘敹鍙栵級銆佹粦鐐广€佹渶浣?5 鍏冭鍒欙紱
  - 鍒嗙孩閫佽浆锛氬湪寮€鐩樺墠璋冩暣鎸佷粨鑲℃暟銆佸潎浠蜂笌鐜伴噾锛?
  - T+1 缁撶畻锛氭敹鐩樺悗鍚屾 `sellable_shares = total_shares`锛?
  - 鍐荤粨鐜伴噾锛氭寕鍗曞崰鐢ㄧ殑鐜伴噾鍦ㄦ垚浜ゆ垨鎾ゅ崟鍚庨噴鏀俱€? 
- 鐘舵€佸瓧娈碉細`cash`, `frozen_cash`, `positions`, `total_equity`, `nav_history`銆?

### 4.7 Analyzer / Reporter
- 杈撳叆锛歚AccountState` 鏃堕棿搴忓垪銆乣Fills`, `Orders`銆? 
- 杈撳嚭锛氭寚鏍囦笌鍙鍖栵細鎬绘敹鐩娿€佸勾鍖栥€佹尝鍔ㄣ€佹渶澶у洖鎾ゃ€丼harpe/Sortino銆丆almar銆佽儨鐜囥€佹崲鎵嬬巼銆佸洜瀛愭毚闇诧紱鍩哄噯瀵规瘮 Alpha/Beta銆? 
- 宸ョ▼瑕佺偣锛?
  - 鎸囨爣璁＄畻闇€鍩轰簬瀵归綈鐨勪氦鏄撴棩鍘嗭紱
  - 鍙€夊鍑?CSV/JSON锛屾垨鐢熸垚鍥捐〃銆?

### 4.8 CostModel / Slippage
- 浣ｉ噾锛氬弻杈硅垂鐜囷紝鍚渶浣?5 鍏冭鍒欍€? 
- 鍗拌姳绋庯細浠呭崠鍑轰晶鏀跺彇銆? 
- 婊戠偣锛氬彲閫夊父鏁颁环宸€佹瘮渚嬩环宸€佹垨鍩轰簬鎴愪氦棰?鐩樺彛娣卞害鐨勫嚱鏁般€? 
- 鍙厤缃細绛栫暐绮掑害鎴栧叏灞€绮掑害銆?

---

## 5. 鏁版嵁妯″瀷涓庢帴鍙ｅ绾?

### 5.1 SignalFrame
- 绱㈠紩锛歚time`, `symbol`銆? 
- 鍊煎煙锛歚[-1,1]` 鎴?`[0,1]`锛宍NaN` 琛ㄧず鏃犱俊鍙枫€? 
- 鏂规硶锛歚to_tensor()`, `align(universe, calendar)`銆?

### 5.2 TargetPortfolio
- 缁撴瀯锛歚{symbol: weight}`, `cash_weight`銆? 
- 瑙勫垯锛氭潈閲嶉潪璐熴€佸悎璁?鈮?1锛涚己鐪侀儴鍒嗚涓虹幇閲戙€?

### 5.3 Order
- 瀛楁锛歚symbol`, `direction (BUY/SELL)`, `quantity (lot-aligned)`, `order_type`, `limit_price`, `urgency`, `created_at`銆? 
- 涓嶅彉閲忥細`quantity % 100 == 0`锛涘崠鍗?`quantity <= sellable_shares`銆?

### 5.4 Position
- 瀛楁锛歚symbol`, `total_shares`, `sellable_shares`, `avg_cost`, `last_price`銆? 
- 琛嶇敓锛歚market_value = total_shares * last_price`銆?

### 5.5 AccountState
- 瀛楁锛歚cash`, `frozen_cash`, `positions: Dict[str, Position]`, `total_equity`, `nav`銆? 
- 鏂规硶锛歚position_weight(symbol)`, `cash_ratio`, `update_with_fill(fill)`銆?

### 5.6 CorporateAction
- 瀛楁锛歚symbol`, `ex_date`, `dividend`, `split_ratio`, `rights_issue`銆? 
- 鐢ㄩ€旓細鍦ㄥ紑鐩樺墠鎵瑰鐞嗭紝鏇存柊鎸佷粨涓庡潎浠枫€?

---

## 6. 鏍稿績娴佺▼锛堟寜浜ゆ槗鏃ワ級

1. Pre-Market锛?
   - 璇诲彇鏃ュ巻銆佸垎绾㈤€佽浆骞惰皟鏁存寔浠擄紱
   - 瑙ｅ喕鏄ㄦ棩涔板叆鑷冲彲鍗栥€? 
2. Data Load锛歂exus 鎻愪緵 `ActiveUniverse` 涓庡榻愭暟鎹€? 
3. Signal锛歄racles 鐢熸垚 `SignalFrame`銆? 
4. Decide锛欰rbiter锛堝惈闃叉姈/璋冨害锛夎緭鍑?`TargetPortfolio`銆? 
5. Generate Orders锛欵xecutor 搴旂敤绾︽潫涓庤祫閲戞鏌ワ紝褰㈡垚 `Orders`銆? 
6. Match & Cost锛欱roker 浣跨敤浠锋牸妯″瀷鎴愪氦锛屾墸闄よ垂鐢紝杩斿洖 `Fills`銆? 
7. Update State锛欰ccount 鍐欏叆鐜伴噾銆佹寔浠撱€佸潎浠枫€佸彲鍗栬偂鏁般€? 
8. Record锛欰nalyzer 璁板綍 NAV銆佹寔浠撱€佷氦鏄撱€佹寚鏍囥€? 
9. Roll锛氳繘鍏ヤ笅涓€涓氦鏄撴棩銆?

---

## 7. A 鑲＄壒鏈夎鍒?

- T+1锛氬崠鍑洪渶浣跨敤 `sellable_shares`锛屾敹鐩樺悗鍚屾銆? 
- 鏁存墜锛氭暟閲忓悜涓嬪彇鏁村埌 100 鑲★紱闆惰偂浠呭湪鍏ㄩ儴鍗栧嚭鏃跺厑璁搞€? 
- 娑ㄨ穼鍋滐細娑ㄥ仠涓嶄拱锛岃穼鍋滀笉鍗栵紙鍙€氳繃閰嶇疆鍏佽鎵撴澘绛栫暐锛夈€? 
- 鍒嗙孩閫佽浆锛氫娇鐢ㄧ湡瀹炰环鏍?+ 浜嬩欢璋冩暣锛屼笉浣跨敤澶嶆潈浠锋牸鍥炴祴锛涘悓姝ヨ皟鏁村潎浠枫€? 
- 鎴愪氦鏃ュ巻锛氱粺涓€浣跨敤浜ゆ槗鎵€鏃ュ巻锛岃繃婊よ妭鍋囨棩涓庝复鍋溿€? 
- 璧勯噾鏍￠獙锛氫拱鍏ュ墠棰勫崰鐜伴噾锛涙垚浜ゅ悗閲婃斁鏈敤閮ㄥ垎銆?

---

## 8. 鎴愭湰涓庢粦鐐规ā鍨?

- `commission_rate`: 鍙岃竟璐圭巼锛沗min_commission`: 5 鍏冦€? 
- `stamp_duty_rate`: 浠呭崠鍑轰晶銆? 
- `slippage`: `f(side, price, notional, adv)`锛岄粯璁ゅ父鏁版垨姣斾緥銆? 
- 鍙彃鎷旓細鏀寔绛栫暐绾ф垨鍏ㄥ眬娉ㄥ唽锛涙敮鎸佸洖鏀炬垚浜よ褰曚互鏍″噯鍙傛暟銆?

---

## 9. 椋庨櫓涓庤皟浠撴帶鍒?

- 鍗曠エ涓婇檺锛歚max_weight_per_symbol`锛堝 20%锛夈€? 
- 鏁翠綋鏉犳潌锛歚sum(weights) <= 1`锛堟棤铻嶈祫鍦烘櫙锛夈€? 
- 鎹㈡墜鐜囬槇鍊硷細`|target-current| < eps` 鏃朵笉浜ゆ槗銆? 
- 榛戝悕鍗曪細鍋滅墝銆侀€€甯傘€丼T 鍒楄〃杩囨护銆? 
- 鐜伴噾搴曠嚎锛氫繚鐣欐渶灏忕幇閲戞瘮渚嬩互瑕嗙洊璐圭敤涓庢粦鐐广€? 
- 瑙﹀彂鍣細甯傚満椋庨櫓淇″彿瑙﹀彂闄嶄粨鎴栨竻浠擄紙鎺╃爜寮忛棬鎺э級銆?

---

## 10. 閰嶇疆涓庢墿灞曟€?

- Plan 閰嶇疆锛歚universe`, `Factors`, `Scoring`, `scheduler`, `Execution`, `broker`, `cost_model`, `slippage_model`, `benchmark`, `start/end_date`銆? 
- 搴忓垪鍖栵細YAML/JSON + Python 绫汇€? 
- 鎻掓嫈锛氭墍鏈夋ā鍧楅€氳繃鎺ュ彛/鎶借薄鍩虹被绾︽潫锛屾浛鎹笉鐮村潖鍏朵粬灞傘€?

---

## 11. 鏈哄櫒瀛︿範婕旇繘璺嚎

1. 瑙勫垯闃舵锛?
   - Factors 涓烘妧鏈?鍩烘湰闈㈣鍒欙紱Scoring 涓虹嚎鎬у姞鏉?+ 闂ㄦ帶銆? 
2. 鐩戠潱瀛︿範锛?
   - Factors 浣滀负鐗瑰緛鐢熸垚鍣紱Scoring 鐢ㄦ爲妯″瀷/绾挎€фā鍨嬮娴嬫湡鏈涙敹鐩婏紝鍐嶇粡鍧囧€兼柟宸垨椋庨櫓棰勭畻姹傛潈閲嶃€? 
3. 寮哄寲瀛︿範锛?
   - 鐜锛歋tate = (SignalFrame, AccountState)锛孉ction = 鐩爣鏉冮噸/璁㈠崟锛孯eward = 骞村寲鏀剁泭鎴?Sortino銆? 
   - 鍏煎锛氫繚鎸佽緭鍏ヨ緭鍑哄绾︼紝Execution/Broker 涓嶅彉銆?

---

## 12. 鍙娴嬫€т笌鎬ц兘

- 鏃ュ織锛氭ā鍧楃骇鏃ュ織锛堟暟鎹€佷俊鍙枫€佸喅绛栥€佽鍗曘€佹垚浜ゃ€佹垚鏈€佸紓甯革級銆? 
- 鎸囨爣锛氳绠楄€楁椂鍒嗗竷銆佸懡涓巼銆佹垚浜ょ巼銆佹崲鎵嬨€佽垂鐢ㄥ崰姣斻€? 
- 璧勬簮锛氭壒閲忓洖娴嬫敮鎸佸杩涚▼/澶氱嚎绋嬶紱缂撳瓨鍥犲瓙璁＄畻缁撴灉銆? 
- 澶辫触绛栫暐锛氭暟鎹己澶便€佷环鏍艰秺鐣屻€佽祫閲戜笉瓒虫椂鐨勯檷绾т笌鍛婅銆?

---

## 13. 娴嬭瘯瑕佹眰

- 鍗曞厓娴嬭瘯锛?
  - 鍥犲瓙杈撳嚭鑼冨洿涓庣己澶卞€煎鐞嗭紱
  - Scoring 鏉冮噸褰掍竴鍖栦笌闃叉姈閫昏緫锛?
  - Execution 绾︽潫锛堟暣鎵嬨€乀+1銆佹定璺屽仠銆佽祫閲戯級锛?
  - 鎴愭湰妯″瀷鏈€灏忚垂鐢ㄤ笌鍗拌姳绋庤鍒欍€? 
- 闆嗘垚娴嬭瘯锛?
  - 鍒嗙孩閫佽浆鍥炴斁锛?
  - 鍏稿瀷绛栫暐鏃ュ唴娴佺▼鍥炴斁锛堝惈绌轰粨銆佹弧浠撱€侀儴鍒嗘垚浜わ級锛?
  - 涓嶅悓璋冨害棰戠巼鐨勭粨鏋滀竴鑷存€с€? 
- 鍥炴祴瀵规瘮锛氫笌鍩哄噯瀹炵幇锛堝绠€鍖?Excel/鑴氭湰锛夊璐︼紝璇樊闃堝€兼槑纭€? 
- 鎬ц兘鍩虹嚎锛氱粰鍑哄崟鏃ャ€佸崟绛栫暐鐨勮€楁椂鐩爣涓庤祫婧愬崰鐢ㄩ槇鍊笺€?

---

## 14. 鍙傝€冧吉浠ｇ爜

```python
def run_plan(plan: Plan):
    account = AccountState.init(plan.initial_cash)
    calendar = load_calendar(plan.start, plan.end)
    for day in calendar:
        account.apply_corporate_actions(day)
        data, universe = nexus.load(day)
        signals = {o.name: o.compute(data, universe) for o in plan.Factors}
        target = plan.Scoring.decide(signals, account)
        if target is None:
            analyzer.record(day, account)
            continue
        orders = plan.Execution.generate(target, account, data.prices)
        fills = plan.broker.match(orders, data.prices, plan.cost_model)
        account.update(fills)
        analyzer.record(day, account, orders, fills)
    return analyzer.report()
```

---

## 15. 鏈琛?

- SignalFrame锛氭寜鏃堕棿涓庢爣鐨勭储寮曠殑淇″彿鐭╅樀銆? 
- TargetPortfolio锛氱洰鏍囨寔浠撴潈閲嶉泦鍚堛€? 
- Order/Fills锛氫笅鍗曟寚浠?/ 瀹為檯鎴愪氦缁撴灉銆? 
- AccountState锛氳祫閲戜笌鎸佷粨鐨勫敮涓€鐪熺浉婧愩€? 
- CostModel/Slippage锛氳垂鐢ㄤ笌婊戠偣璁＄畻缁勪欢銆? 
- Analyzer锛氱哗鏁堜笌鏃ュ織杈撳嚭妯″潡銆?

