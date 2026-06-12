# 四川高考招生信息抓取和整理

教育部在网上公布的各类招生信息特点为：

- 信息是图片方式，无法直接拷贝和粘贴文字信息。
- 图片有水印，增加文字识别难度。

这增加了对所有学校招生信息进行汇总，统计的难度。因此需要对不同网站，不同类型的招生信息，具体分析，然后进行图片抓取和文字识别。

## 2025四川省高考招生信息

历史类：[https://plan.sceea.cn/wkjh.html](https://plan.sceea.cn/wkjh.html)

物理类：[https://plan.sceea.cn/lkjh.html](https://plan.sceea.cn/lkjh.html)

汇总了所有高校在四川省的招生专业和招生人数。

通过在浏览器里打开开发者工具，切换到network，并在网页上点击“上一页”和“下一页”进行翻页，可以看到所有页面信息为gif图片。

历史类第一页为：

[https://plan.sceea.cn/img/wk/wk%20(1).gif](https://plan.sceea.cn/img/wk/wk%20(1).gif)

后面每页网站一次增加括号里的数字。最后一页为：

[https://plan.sceea.cn/img/wk/wk%20(140).gif](https://plan.sceea.cn/img/wk/wk%20(140).gif)

物理类第一页：

[https://plan.sceea.cn/img/lk/lk%20(1).gif](https://plan.sceea.cn/img/lk/lk%20(1).gif)

最后一页：

[https://plan.sceea.cn/img/lk/lk%20(232).gif](https://plan.sceea.cn/img/lk/lk%20(232).gif)

下面是信息提取和结构化的流程。

## Step 1
从网络上下载考试报的所有页面。保存在目录"01.raw.gif"中。历史类和物理类分别保存在子目录"history"和"physics"中。以下各步骤文件保存的方式与此相同。

## Step 2
根据AI的建议，将所有原始gif图片转化为png格式，以便于后面各个步骤中对图片文件做进一步处理。转换后的图片保存在目录"02.png.format"中。

## Step 3
去掉
