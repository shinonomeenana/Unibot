# 分布式客户端使用文档
使用此客户端, 您可以用自己的QQ号搭建一个Unibot

## 准备工作
::: warning 注意

部署本项目需要一定的电脑基础，会读文档

该教程已经过大量用户验证无问题，一步步跟着走就能部署好。如果出现问题建议先排除自己的问题，或者到分布式用户群里问问群友怎么解决

:::

### 获取一台服务器
你需要一台24h不关机的电脑，否则关机这段时间bot将无法工作

Windows 电脑需要运行大于等于 Windows 8 或 Windows server 2012 版本的系统（更低版本实测无法运行）
Linux 有 Ubuntu 20.04 (Python 3.8) 和 Ubuntu 22.04 (Python 3.10) 打包的两个版本，建议使用 Ubuntu 20 或以上系统，在较低版本 Ubuntu 和其他较低版本 linux 中可能提示缺少 GLIBC 对应版本，安装非常麻烦，不推荐使用。
当然，你也可以通过Docker来绕过这一问题。

### 下载客户端和申请token
请加群467602419在群文件下载客户端，按照群公告的步骤自助申请token

## 配置客户端
你需要将客户端放在一个文件夹内，在这个文件夹下新建一个`token.yaml`，用你喜欢的编辑器打开，填上以下的设置
```yaml
token: xxxxxx
port: 2525
blacklist:
- 123456
- 234567
whitelist:
- 345678
pjskguesstime: 50
charaguesstime: 30
superuser:
- 123456
```
其中，`token` 填写申请的token，`port` 填写你要通信的端口号，不懂可直接填写`2525`，如果你有要关闭bot的群，则需要按照格式配置 `blacklist` 项，不需要可以删除只保留上面两行。

模拟抽卡，猜曲，看卡图等功能需要添加 `whitelist` 项，并填入白名单群号。以上配置如果改动需要重启客户端生效

猜曲时间，猜卡面时间可自定义，如无需要可不配置。

`superuser`可以填写你自己的QQ号，配置了`superuser`的QQ号可使用如下指令：

- `添加群白名单[群号]`：添加群到`whitelist`
- `删除群白名单[群号]`
- `添加群黑名单[群号]`：添加群到`blacklist`
- `删除群黑名单[群号]`
- `添加管理员[QQ号]`：添加QQ号到`superuser`
- `删除管理员[QQ号]`
- `关闭分布式`，`开启分布式`：此命令群主/管理员也可以使用

准备就绪后可尝试启动客户端，如果没有问题会显示如下日志

```text
[xxxx-xx-xx xx:xx:xx,xxx] Running on http://127.0.0.1:2525 (CTRL + C to quit)
```

::: warning 注意

不要关闭客户端，必须启动客户端才能使用 bot

:::

## 配置 GO-CQHTTP

### 下载 [GO-CQHTTP](https://github.com/Mrs4s/go-cqhttp/releases)

如果上面的链接无法打开，你也可以在群文件下载

>如果你不知道这是什么，善用搜索引擎.

### 使用反向 WebSocket
打开 cqhttp 按提示创建bat文件，打开后, 通信方式选择: 反向WS

在 CQHTTP 配置文件中，填写 `ws_reverse_url` 值为 `ws://127.0.0.1:你的端口/ws/`，这里 `你的端口` 应改为上面填的端口号。

然后，如果有的话，删掉 `ws_reverse_event_url` 和 `ws_reverse_api_url` 这两个配置项。

最后的连接服务列表应该是这样的格式
```yaml
# 连接服务列表
servers:
  # 添加方式，同一连接方式可添加多个，具体配置说明请查看文档
  #- http: # http 通信
  #- ws:   # 正向 Websocket
  #- ws-reverse: # 反向 Websocket
  #- pprof: #性能分析服务器
  # 反向WS设置
  - ws-reverse:
      # 反向WS Universal 地址
      # 注意 设置了此项地址后下面两项将会被忽略
      universal: ws://127.0.0.1:2525/ws/
      # 重连间隔 单位毫秒
      reconnect-interval: 3000
      middlewares:
        <<: *default # 引用默认中间件
```

之后，在确保客户端已打开的情况下，打开cqhttp，按提示登录qq后，客户端应该会出现一行这样的日志
```text
[xxxx-xx-xx xx:xx:xx,xxx] 127.0.0.1:xxxxx GET /ws/ 1.1 101 - 515
```

## 测试对话

在有机器人的群里发送命令，比如`sk`，如果一切正常，ta 应该会回复你。

如果没有回复，请检查客户端运行是否报错、cqhttp 日志是否报错。如果都没有报错，则可能是机器人账号被腾讯风控，需要在同一环境中多登录一段时间。

## Docker部署

若不方便使用支持的操作系统，可尝试通过docker部署bot。

首先，拉取ubuntu22.04镜像
```bash
docker pull ubuntu:22.04
```

将编辑好的配置文件、SSL证书（如需要）放在bot可执行文件的同级目录中，新建Dockerfile。若不需要SSL证书，删除`COPY _.unipjsk.com.crt`行及其后两个`RUN`指令。
```dockerfile
FROM ubuntu:22.04

COPY bot-3.1.0-cpython-310-x86_64-linux-gnu /usr/local/bin/
COPY token.yaml /
COPY _.unipjsk.com.crt /usr/local/share/ca-certificates/
RUN apt-get update && apt-get install -y ca-certificates
RUN update-ca-certificates

ENTRYPOINT ["/usr/local/bin/bot-3.1.0-cpython-310-x86_64-linux-gnu"]
```

生成镜像并启动服务
```bash
docker build -t unibot .
docker run --network=host unibot
```

此时服务将在设定好的端口运行，若提示SSL出错，请在开发机浏览器访问并导出`unibot-api.unipjsk.com`证书信息，然后重复上述操作。
