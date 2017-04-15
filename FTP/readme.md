#FTP

##版本v2
  bug修复：

    1）.修复连续两次cd../之后无法返回上级目录的bug

    2）修复参数之间多个空格导致参数异常bug

  功能改进：
    1) 添加用户判断是否选择断点续传的功能
    2）添加 用户上传和下载自定义文件名的功能
    3) 修改判断断点续传的逻辑,采用判断临时文件的方法,更加准确灵活,不再依赖日志
    4) 修改记录日志的内容,将日志改为整体记录到ftp.log中,当然,也可以自己定义log名
    
##1.ftp功能[介绍]
>用户加密认证
>允许多用户同时登录，但是不能互访数据目录
>自定义空间配额
>上传文件  put
>下载文件  get
>删除文件或目录  rm
>创建目录  mkdir
>移动文件目录  mv
>查看当前路径  pwd
>列出指定目录下的内容 ls
>切换目录  cd
>md5校验，保证上传下载文件一致性
>人性化进度条
>断点续传

##2.need environment[环境需求]
`Python版本 >= Python3.0`

##3.move[移植问题]
不兼容windows

##4.important .py[文件说明]
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


##5.how to[怎么执行]
>* python3 bin/client.py     客户端运行
>* python3 bin/server.py	start 服务端运行
>* python3 bin/server.py adduser 添加用户

##6.测试账号及密码
用户1
    账号：zhf
    密码：123

也可以自行添加

##7.配置文件说明:
    userdb 文件存放用户账户密码,密码采用md5加密,可以自行创建和添加,也可以使用adduser参数添加
    ftp.conf  ftp的配置文件
    参数说明:
        [global]
        ip = 127.0.0.1     ftp监听的ip地址
        port  = 8000        ftp端口
        userdb = conf/userdb    用户密码文件
        data = data         #用户数据目录
        logs = logs         #用户日志目录
        quota_size = 200       #默认空间配额 单位是M

     用户自定义空间配额:
        [zhf]
        quota_size = 10      #当用户自定义配额之后,自定会生效
##8.运行说明：
> 1) connect
    连接ftp   ip为127.0.0.1 端口8000, 根据实际配置文件来定
> 2) put
    put 本地文件  ftp目标目录
> 3) get
    get ftp文件  本地目录
> 4) ls
     ls  查看当前目录下
     ls  ../  查看上一级目录
> 5) cd
    cd  file/file1  进入file/file1目录
    cd ../ 返回上一级目录
> 6) rm
    rm  文件或者目录  删除文件或目录   注意:只能删除当前目录下或子目录下
> 7) mkdir
    mkdir 目录  创建目录
> 8) mv
    mv  源文件  目标文件     移动文件,如果在同一级目录,则视为重命名
    



