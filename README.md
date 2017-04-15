# FTP
python实现FTP上传下载


一.ftp功能：
  1.用户加密认证
  2.允许多用户同时登录，但是不能互访数据目录
  3.自定义空间配额
  4.上传文件  put
  5.下载文件  get
  6.删除文件或目录  rm
  7.创建目录  mkdir
  8.移动文件目录  mv
  9.查看当前路径  pwd
  10.列出指定目录下的内容 ls
  11.切换目录  cd
  12.md5校验，保证上传下载文件一致性
  13.人性化进度条
  14.断点续传
  

2.目录树：
  FTP/
  ├── __init__.py
  ├── bin		＃入口文件目录
  │   ├── __init__.py
  │   ├── client.py			#客户端入口文件
  │   └── server.py			＃服务端入口文件
  ├── conf		＃配置文件目录
  │   ├── __init__.py
  │   ├── ftp.conf		＃ftp配置文件
  │   └── userdb				＃用户账户密码文件
  ├── core    ＃核心目录
  │   ├── __init__.py
  │   ├── base.py			＃初始化脚本，自动解析加载配置信息
  │   ├── common.py			＃公共函数库
  │   ├── ftpclient.py	＃ftp客户端功能类
  │   └── ftpserver.py	＃ftp服务端功能类
  ├── data		＃用户数据目录
  │   ├── __init__.py
  │   ├── zhf			＃zhf用户数据目录
  │   
  └── logs		＃logs目录
      ├── __init__.py
      ├── ftp.log		＃ftp服务器log

  3.运行
    #python3 bin/client.py     客户端运行
    #python3 bin/server.py	start 服务端运行
    #python3 bin/server.py adduser 添加用户
    
    
    
