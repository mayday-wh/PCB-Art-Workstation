# PCB Art Assistant | PCB 艺术加工助手

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

在翻看一些喜欢的漫画和浮世绘时，经常会冒出一个念头：如果这些线条不只是存在于屏幕或纸张上，而是通过沉金、喷锡、绿油和丝印，永远‘刻’在电路板（PCB）上，会是什么样子？

想法付诸实践，有了这个下面的项目，一个将普通位图转化为 PCB 物理层的 PC 端小工具。它可以帮助你将普通的彩色图片转化为符合 PCB 生产工艺（如丝印、阻焊、铜箔层）的黑白分色图。

从 [Releases](../../releases) 页面下载最新版本的压缩包，双击  `.exe`  即可直接运行。使用方法见下文的功能模块介绍。

## 🌟 实物展示

下面展示的两个案例是初期的实验品，由于单纯艺术板在嘉立创打样有限制，无法使用免费券，所以把灯板的电路整合在了同一块电路板上，使用TTP223触控芯片实现点击开关背光板。

<p align="center">
  <img width="50%" alt="案例green" src="https://github.com/user-attachments/assets/1c865312-a8c2-413d-bdde-96b294376377" />
</p>

<p align="center">
  <img width="50%" alt="案例blue" src="https://github.com/user-attachments/assets/a8b95dff-d71a-4a3a-83f4-839b2c12bdd4" />
</p>

## 🌟 功能模块介绍

1.  **色卡录入**

要把一张颜色复杂的图片变成 PCB 上的图层，首先需要知道PCB能实现哪些颜色。

用S代表丝印层， M代表阻焊层， L代表喷锡层， B代表底层， T代表顶层，由于喷锡层上面不能直接丝印，所以单面有7种排列组合，如下图所示，在顶层横向放置7种组合，在底层纵向放置7种组合，就能模拟层叠加的所有组合。

<p align="center">
<img width="30%" alt="层的排列组合" src="https://github.com/user-attachments/assets/69b8fac4-baff-43ce-b879-9cb124f66a73" />
</p>

经过打样测试（蓝色阻焊 + 有铅喷锡），无背光的色彩很单调，有背光才能展示 PCB_Art 。

如下图所示，只要有L（喷锡层）就不透光，所以只有右上角 4x4 的排列方式可以透光，这些颜色极大丰富了色卡。

<p align="center">
<img width="50%" alt="颜色的排列" src="https://github.com/user-attachments/assets/9bde5043-c479-4498-85a4-8a7aaceed863" />
</p>

下一步就是在 <b>色卡录入</b> 界面录入能实现的色彩及每种色彩对应的层关系。

首次运行软件，会在 .exe 目录生成 colors.json 文件，用于存储色卡信息，色卡绑定阻焊颜色（绿、蓝、红、紫、黄、白、黑）和展示模式（有/无背光）。

 [Releases](../../releases) 页面提供的软件压缩包，包含录入了部分色卡信息的 colors.json 文件。

色卡可以自行增删色块，色块可以从颜色盘选取，也可以从导入照片选取，对应的层组合勾选正确即可，保存色块时会按照层组合去重，防止同一层组合重复录入多种颜色。

<p align="center">
<img width="50%" alt="色卡录入" src="https://github.com/user-attachments/assets/17633a43-7241-45eb-a0d6-c8a6a537822f" />
</p>

色卡列表使用 7 根粗竖线显示层组合，包含的层用深色标识，不包含的层用浅色。

2.  **色彩聚集**

在 <b>色彩聚集</b> 界面，选择阻焊颜色，有/无背光，点击 <b>提取色卡</b> ，即可导入相应色卡，然后在导入的图片中选取你分别想要映射的颜色。

如果载入图片比较单调，色卡中用不到的颜色无需映射，空着即可。误选的话，可以点击后面的取消。

点击 <b>效果预览</b> ，可以看到近似成品观感的效果图。

<p align="center">
<img width="50%" alt="色彩聚集" src="https://github.com/user-attachments/assets/0efca58f-4e8d-4bd1-a7ad-7138e328eaa7" />
</p>

此外， <b>色彩聚集</b> 模块还整合了 <b>原点标定设置</b> 和 <b>导出降噪设置</b> 。

折腾过 PCB 艺术画的朋友都知道，多图层导入 EDA 时，对齐位移简直是噩梦。我添加了一个 <b>原点标定设置</b> 的小功能。

在色彩聚类模块的菜单栏，可以看到原点标记设置，可选择在图片的角落（可多选，通常左上就可以）添加了一个默认长度是图片 1/100 宽度的三角形锚点，它刚好藏在 PCB 板框的倒圆角里。

并且在 EDA 插入图片时，锁住原点（0，0）。成品出来后，这些标记点又会被倒角完美切除，不留痕迹。

点击 <b>导出图纸</b> 会自动导出物理层的图纸，如果噪点较多可以勾选 <b>导出降噪设置</b> 。

未涉及的层不会导出，图纸带有编号，对应关系如下：TS-顶层丝印, TM-顶层阻焊, TL-顶层, BL-底层, BM-底层阻焊, BS-底层丝印。

<p align="center">
<img width="50%" alt="导出结果" src="https://github.com/user-attachments/assets/765c9696-38e6-4ddd-986c-e898b573c4ab" />
</p>

需要注意的是，在立创EDA的相应层插入图片需要选择 <b>反相</b> ，底层图片（BL-底层, BM-底层阻焊, BS-底层丝印）需要左右翻转。

如果你也正好喜欢绘画，又恰巧是个电子爱好者，希望这个工具能帮你省去一些繁琐的步骤。
