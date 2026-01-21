维护因子表；现在左侧的factors标签页应该在启动时读取本地的因子列表及其需要的参数（位于./data/settings.json中，factors字段）。与Symbols的操作逻辑类似，在双击后，中间的标签页Chart不再是纯K线图，而应该是一个新的面板，它能够该因子的说明文本对应json文件中的help字段内容。

---

小bug：

File菜单栏Run Backtest应该在Exit的下面

关闭Plan以后，所有的CI和GI应该都清空

在factors/symbols页面做了双击操作以后，中间的标签页应该对应的自动切换到那个页面

预览K线不再支持拖动的方式打开，移除中间chart页面的提示文本“Double-click or drag to view K-line”

---

重构：
所有的控件都应该有一个独立的py文件。