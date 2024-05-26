# 自助上传用户数据

>  本文档仅支持ios设备

>  上传的数据是抓包时间点的个人用户数据，后续如果数据有更新需要重新抓包

::: danger 警告
由于目前b30已毫无参考性，不建议为了看b30费劲上传数据
:::


## 方法1：已失效
<!-- 
配置文件 by 希凪(Kinagi)

### 仅Unibot可读

QX: https://assets.unipjsk.com/mitm/suite_private.conf

Surge/小火箭: https://assets.unipjsk.com/mitm/suite_private.sgmodule

Loon: https://assets.unipjsk.com/mitm/suite_private.lnplugin

### 公开API读取

QX: https://assets.unipjsk.com/mitm/suite_public.conf

Surge/小火箭: https://assets.unipjsk.com/mitm/suite_public.sgmodule

Loon: https://assets.unipjsk.com/mitm/suite_public.lnplugin


::: tip 

只提供小火箭的教程，使用其他软件的一般都会自己添加重写配置和安装证书

:::

### 小火箭抓取教程（以公开读取为例）

点击下方配置，再点击右上角加号
![sr1](/sr1.jpg)

输入 `https://assets.unipjsk.com/mitm/suite_public.sgmodule` 后点击下载
![sr3](/sr3.jpg)

选择刚刚下载的新配置，点击使用配置
![sr4](/sr4.jpg)

点击刚刚下载的新配置右边的i按钮，进入`HTTPS 解密`
![sr6](/sr6.jpg)

打开`HTTPS 解密`
![sr7](/sr7.jpg)

软件会弹出证书，点击生成新的CA证书
![sr8](/sr8.jpg)

点击安装证书
![sr9](/sr9.jpg)

点击允许
![sr10](/sr10.jpg)

在设置中点击新出现的已下载描述文件
![sr11](/sr11.jpg)

安装该描述文件
![sr12](/sr12.jpg)

然后进入 **通用-关于本机-证书信任设置** 打开刚刚的证书开关，这一步不要漏！

然后打开代理开关。如果你的网络不能直连，需切换到可以登录游戏的节点将`全局路由`改为`代理`

进入游戏即上传成功

成功后请将配置切换回你日常使用的配置，该抓包用配置不带任何分流规则 -->


## 方法2：自行抓包

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