# 自助上传用户数据

>  本文档仅支持ios设备

>  上传的数据是抓包时间点的个人用户数据，后续如果数据有更新需要重新抓包（和maimai查分器差不多）

::: danger 注意

安卓版app内置了证书验证，常规方法无法抓包。已知的抓包方法无法隐藏root，游戏会自动上报root信息，非常危险，不推荐任何人尝试使用。且绝对不要尝试修改apk，游戏会自动上报apk签名，与官方不一致可能会有封号风险。

:::

软件下载：<https://apps.apple.com/app/id1585539533>

打开软件 点击证书管理
![suite1](/suite1.jpg)

按照提示安装并信任(请用safari打开这个页面)

安装好之后请确认软件显示证书状态为**已信任**
![suite2](/suite2.jpg)

打开抓包 打开游戏 **从最开始的标题页面进入游戏**后返回抓包软件，关闭抓包

找到 `api/suite/user/xxxx` 比较大的那个
![suite3](/suite3.jpg)

选择响应 点击响应体
![suite4](/suite4.jpg)

右上角导出 导出原始数据 建议保存到文件
![suite5](/suite5.jpg)
![suite6](/suite6.jpg)

在 <https://suite.unipjsk.com/> 上传刚刚保存的文件
![suite7](/suite7.jpg)

成功