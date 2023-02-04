我要和虹夏结婚！
lofterSpiderRobot.py 是一个用于获取lofter上图片并推送到企业微信机器人的脚本
实现参考了 https://github.com/IshtarTang/lofterSpider 的项目做了一定简化

# 环境搭建
命令行输入

pip3 install requests

下面的不一定需要

pip3 install lxml

pip3 install urllib3

pip3 install json5

pip3 install html2text

pip3 install numpy

# 使用方法：
修改url为lofter中需要获取图片的url，填写自己的企业微信机器人webhook，填写保存文件的路径

```python
if __name__ == '__main__':
    # 基础设置  -------------------------------------------------------- # 爬这个url下的图片推送到企业微信，后续做回调改url即可
    url = "https://www.lofter.com/tag/%E8%99%B9%E5%A4%8F/total"

    #企业微信机器人webhook
    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=acda49fc-e178-4157-a3c3-5ef279bb3a71'

    # 文件设置  -------------------------------------------------------- #
    # 运行中产生的文件和保存文件的存放路径
    file_path = "/Users/jookerma/Pictures"

    force_refresh = 0

    # 主逻辑入口
    run(url, webhook, force_refresh, file_path)
```

命令行输入python3 lofterSpiderRobot.py 即可
会推送按照tag获取的图片到企业微信上，执行一次推送一组数据
后续会优化成定时任务
