jj# pornbot91_py
91 | 好色 | 麻豆 视频下载，发送电报


 [English](./README_en.md) 

###  特点

好色视频链接支持（补充作者删除的视频）

**尽量异步的方式处理,下载速度大幅提升**,实测很快(100M视频,下载+合并用时18秒)

兼容旧版mp4，现在是m3u8

破解91视频的播放限制、理论上可以无限下载

为标题添加中文分词标签，解决电报对中文搜索的问题

重试机制，网络超时重试

向机器人发送链接，可以 `获取视频真实地址` 并 `下载视频`

docker预装环境，方便更换服务，一键启动

获取91免翻地址


### docker运行



#### 安装 docker
```
curl -fsSL get.docker.com -o get-docker.sh&&sh get-docker.sh &&systemctl enable docker&&systemctl start docker

```

#### 编译docker 镜像

```
docker build -t jwstar/pybot .
```


#### 安装docker-compose（新版docker可以不安装，因为已经集成进去了,命令把 - 去了就行）

```yaml
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose &&chmod +x /usr/local/bin/docker-compose
```


### 配置
创建目录 /pybot
```yaml
mkdir /pybot
```
### 编辑docker-compose.yml

```angular2html
      #windows配置环境变量需要重启电脑
      REDIS_HOST: 11.11.22.333
      REDIS_PORT: 16379
      REDIS_PASS: 424243
      API_ID: 21231221
      API_HASH: *************************
      BOT_TOKEN: *****:**************************
      #定时任务发送的群组id(@get_id_bot,可以在这里获取到)
      GROUP_ID: 121231311
```

### 启动项目

```yaml
docker-compose up
docker-compose up -d #后台运行
或者
docker compose up 
docker compose up -d #后台运行
```




### 本地运行
python3.10以上
```
pip install -r requirements.txt
```

修改代理

```
python pornbot.py
```


### 测试

1.发送 /start 到机器人

得到回复  `********`

发送链接测试

 ![image](https://user-images.githubusercontent.com/48782751/159890884-d65a2528-e7fc-4be3-a981-fa7608072467.png)

### 服务部署注意

telegram会根据手机号绑定的dc来选择上传点，亚洲手机号一般会在telegram的dc5(新加坡)，美国手机号建议选择美国的vps来挂bot

推荐服务器(选lite版即可)：https://www.dmit.io/aff.php?aff=4782


