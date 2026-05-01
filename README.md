# PCB Art Workstation | PCB 艺术加工一体化工作站

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

在翻看一些喜欢的漫画和浮世绘时，经常会冒出一个念头：如果这些线条不只是存在于屏幕或纸张上，而是通过沉金、喷锡、绿油和丝印，永远‘刻’在电路板（PCB）上，会是什么样子？

想法付诸实践，有了这个下面的项目，一个将普通位图转化为 PCB 物理层的 PC 端小工具。它可以帮助你将普通的彩色图片转化为符合 PCB 生产工艺（如丝印、阻焊、铜箔层）的黑白分色图。

从 [Releases](../../releases) 页面下载最新版本的 `.exe` 文件，双击即可直接运行。使用方法见下文的功能模块介绍。

## 🌟 实物展示

下面展示的两个案例是初期的实验品，由于单纯艺术板在嘉立创打样有限制，无法使用免费券，所以把灯板的电路整合在了同一块电路板上，使用TTP223触控芯片实现点击开关背光板。

<p align="center">
  <img width="40%" alt="案例green" src="https://github.com/user-attachments/assets/1c865312-a8c2-413d-bdde-96b294376377" />
</p>

<p align="center">
  <img width="40%" alt="案例blue" src="https://github.com/user-attachments/assets/a8b95dff-d71a-4a3a-83f4-839b2c12bdd4" />
</p>

## 🌟 版本V2.1功能模块介绍

V2.1集成四个模块，构成完整的 PCB 图像处理流水线：

1.  **色彩聚类映射 (Color Mapping)**

要把一张颜色复杂的图片变成 PCB 上的图层，首先得学会精简。所以第一步就是色彩聚类映射，颜色选择很重要。此处使用鼠标点击吸取原图自带的颜色，来设置色卡。

设置色卡时，可以选1个最深色（黑色）、1个最浅色（白色）、2个主体色（深浅蓝/绿等），再选1个阴影色（灰色）和1个亮色（亮黄），自由搭配。

经过处理，复杂的画面降维成 5-6 种极简的色块。这种方式处理后的图片，有点波普艺术的风格。


<p align="center">
  <img width="60%" alt="UI预览1" src="https://github.com/user-attachments/assets/5ac30593-fdf3-40ae-9e05-b190f8a2d17b" />
</p>

2.  **自动分色提取 (Color Separation)**

识别图片中的唯一颜色。一键将各颜色区域分离，生成独立的黑底白图。

<p align="center">
  <img width="60%" alt="UI预览2" src="https://github.com/user-attachments/assets/24cd04e4-7925-473d-afbb-1184740d3eb7" />
</p>

3.  **逻辑运算去噪 (Logic Synthesis)**

将步骤2得到的黑白图层进行合并运算，分别合成顶层丝印，顶层，顶层阻焊，底层，底层阻焊（Mask），直接对接 PCB 图层素材。

遵循“全黑为黑，有白则白”的逻辑，合并的同时去除噪点。

添加图片的基本思路如下，插入 EDA 后，可以在 3D 预览中查看效果，进行调整。
- 顶层丝印包含白色；
- 顶层包含白色，黑色；
- 顶层阻焊包含较深的主体色，白色，黑色；
- 底层包含黑色和阴影色。

<p align="center">
  <img width="60%" alt="UI预览3" src="https://github.com/user-attachments/assets/d3f17f05-d6c5-4fc9-87a8-5f3f035f3310" />
</p>

4.  **添加宽度标记 (Add Width Anchors)**

折腾过 PCB 艺术画的朋友都知道，多图层导入 EDA 时，对齐位移简直是噩梦。
我添加了一个‘<b><font color="#673AB7">宽度标定</font></b>’的小功能。

在图片左上角和右上角，分别添加了一个默认长度是图片 1/100 宽度的三角形锚点，它刚好藏在 PCB 板框那 2mm 的圆角里。

在 EDA 里导入时，锁住原点（0，0）。成品出来后，这些标记点又会被倒角完美切除，不留痕迹。

<p align="center">
  <img width="60%" alt="UI预览4" src="https://github.com/user-attachments/assets/61000cd8-0bb3-42da-ba8c-a03a4ea1720c" />
</p>

## 🌟 版本V3.1功能模块介绍

版本V3.1对处理逻辑进行了大改，初始设置麻烦了一些，但能在选色聚集后直接生成效果图，并导出6层物理层对应的黑底白图。包含3个模块：

1.  **色卡录入**

- 首次运行软件，会在根目录生成colors.json，用于存储色卡信息，色卡绑定阻焊颜色和展示模式。
- 色卡需要自行写入，颜色可以从颜色盘选取，只要对应的层设置正确即可。可参考下图，进行设置。
- 图片展示的是蓝色有背光的色卡，所以主体色有深蓝和浅蓝，如果用别的阻焊颜色，只需要修改一下颜色，层设置不需改变。

<p align="center">
<img width="60%" alt="色卡录入" src="https://github.com/user-attachments/assets/37464584-5f13-4d0d-83cc-bd0f671bf6c7" />
</p>

2.  **色彩聚类**

- 在色彩聚类模块中，选择蓝色，有背光，即可导入色卡，然后只需要在原图片中选取你分别想要映射的颜色。
- 图片比较单调，不需要色卡中的所有颜色时，空着即可，误选的话，就点击提取色卡，然后重选。
- 预览效果基本与成品差不多，点击导出图纸会自动导出6层物理层的图纸。
- 对应关系如下：TS-顶层丝印, TM-顶层阻焊, TL-顶层, BL-底层, BM-底层阻焊, BS-底层丝印。

<p align="center">
<img width="60%" alt="色彩聚集" src="https://github.com/user-attachments/assets/f0bcebbb-743c-47b3-9bfd-bba3e7a1d640" />
</p>

3.  **原点标记**

该功能既是版本V2.1模块4个功能，在图片左上角和右上角，分别添加了一个默认长度是图片 1/100 宽度的三角形锚点，未作修改。

如果你也正好喜欢绘画，又恰巧是个电子爱好者，希望这个工具能帮你省去一些繁琐的步骤。
