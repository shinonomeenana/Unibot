<div align="center">
  <img width="256" src="./docs/.vuepress/public/nekoknd.png" alt="logo">


# Unibot
一款基于 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 与 [aiocqhttp](https://github.com/nonebot/aiocqhttp) 的多功能 QQ 群 PJSK 机器人

[使用文档](https://docs.unipjsk.com/) · [交流群](https://qm.qq.com/cgi-bin/qm/qr?k=Osy7KwWvvLWYTjBFJH3MQwkAqgAIV7rT&jump_from=webapi) · [交流频道](https://qun.qq.com/qqweb/qunpro/share?_wv=3&_wwv=128&appChannel=share&inviteCode=7Pe26&appChannel=share&businessType=9&from=181074&biz=ka&shareSource=5)

<span style="font-size:5px">头图 ©SEGA / ©Colorful Palette Inc. / ©Crypton Future Media, INC. www.piapro.net All rights reserved.</span>

</div>

## 提示

本人并非计算机相关专业，代码能力不强，很多地方写得很烂，还请见谅。

## 已实现功能

具体可参考[使用文档](https://docs.unipjsk.com/)

## 关于本项目

该项目依赖的API与本地资源库未公开，无法自行部署，但是你可以尝试使用[分布式客户端](https://docs.unipjsk.com/distributed/)搭建一个Unibot，或者稍微修改一下其中一些功能，移植一些模块到你自己的机器人。

其中推特推送单独开源并配有部署文档：[watagashi-uni/twitterpush](https://github.com/watagashi-uni/twitterpush)

### 关于游戏 API、masterDB 和 游戏资源库

本项目直接调用本地资源，如你的项目需要资源库可使用 [assets.unipjsk.com](http://assets.unipjsk.com/) 或 [Sekai Viewer](https://sekai.best/asset_viewer)、[pjsek.ai](https://pjsek.ai/assets) 的资源库，api 可使用 [api.unipjsk.com/api](https://api.unipjsk.com/api)，使用方法请参考 [Unibot API 使用文档](https://docs.unipjsk.com/API)

masterDB（项目内放在`masterdata`文件夹下） 可使用 [Sekai-World/sekai-master-db-diff](https://github.com/Sekai-World/sekai-master-db-diff)。带玩家游玩数据、难度偏差值的乐曲信息（项目内放在`masterdata\realtime`文件夹下）来自 [pjsekai/database/musics](https://gitlab.com/pjsekai/database/musics)，自动更新可参考`autotask.py`

## 支持与贡献

觉得好用可以给这个项目点个 Star 。

有意见或者建议也欢迎提交 [Issues](https://github.com/watagashi-uni/Unibot/issues) 和 [Pull requests](https://github.com/watagashi-uni/Unibot/pulls)。

## 特别感谢

- [Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp): 基于 [Mirai](https://github.com/mamoe/mirai) 以及 [MiraiGo](https://github.com/Mrs4s/MiraiGo) 的 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) Golang 原生实现 
- [chinosk114514/QQ-official-guild-bot](https://github.com/chinosk114514/QQ-official-guild-bot): QQ官方频道机器人SDK
- [chinosk114514/homo114514](https://github.com/chinosk114514/homo114514): 恶臭数字论证器
- [SkywalkerSpace/emoji2pic-python](https://github.com/SkywalkerSpace/emoji2pic-python): Apple emoji and text to picture
- [pcrbot/5000choyen](https://github.com/pcrbot/5000choyen): 适用hoshino的5000兆円欲しい! style图片生成器插件
- [nonebot/aiocqhttp](https://github.com/nonebot/aiocqhttp): A Python SDK with async I/O for CQHTTP (OneBot).
- [sevenc-nanashi/pjsekai-soundgen](https://github.com/sevenc-nanashi/pjsekai-soundgen): 譜面から音声を生成するツール。
- [noneplugin/nonebot-plugin-imageutils](https://github.com/noneplugin/nonebot-plugin-imageutils): Nonebot2 PIL工具插件

## 权利表记

[sevenc-nanashi/pjsekai-soundgen](https://github.com/sevenc-nanashi/pjsekai-soundgen)

```
プロセカ風譜面音声生成ツール：
  https://github.com/sevenc-nanashi/pjsekai-soundgen
  作成：名無し｡
  Twitter: https://twitter.com/sevenc_nanashi
  YouTube: https://youtube.com/channel/UCv9Wgrqn0ovYhUggSSm5Qtg
```

[chinosk114514/QQ-official-guild-bot](https://github.com/chinosk114514/QQ-official-guild-bot)

```
MIT License

Copyright (c) 2021 chinosk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

[chinosk114514/homo114514](https://github.com/chinosk114514/homo114514)

```
MIT License

Copyright (c) 2022 chinosk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

[SkywalkerSpace/emoji2pic-python](https://github.com/SkywalkerSpace/emoji2pic-python)

```
MIT License

Copyright (c) 2019 sniper-py

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

[nonebot/aiocqhttp](https://github.com/nonebot/aiocqhttp)

```
The MIT License (MIT)
Copyright (c) 2017 Richard Chien

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

[noneplugin/nonebot-plugin-imageutils](https://github.com/noneplugin/nonebot-plugin-imageutils)

```
MIT License

Copyright (c) 2022 MeetWq

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```