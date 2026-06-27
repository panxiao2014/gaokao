附件里的json文件是一个文字扫描提取数据，包含了高考招生信息。

招生信息的组织结构请参考附件physics_template.md。

招生中具体各院校信息，专业组信息和专业组下各专业的招生信息示例请参考school_template.md。

对于如何解析招生信息，各字段提取时的文字模式和规律，请参考tips.md。

现在请根据以上信息，在解析json文件后生成一个markdown文件2025.sichuan.physics.md。规则如下：

1. md文件的模板参考附件physics_template.md；

2. 对于json文件中无法解析，无法通过上下文推段出的字段，在md文件中使用"(待确定)"填充。

