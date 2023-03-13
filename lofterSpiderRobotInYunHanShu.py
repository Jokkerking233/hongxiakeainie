import requests
import re
import os
import time
import json
from urllib import parse

def make_data(url=""):
    """
    :param url:  生成data需要用到url，tag需要的是tag页的url
    :return: 初始data
    """
    base_data = {'callCount': '1',
                 'httpSessionId': '',
                 'scriptSessionId': '${scriptSessionId}187',
                 'c0-id': '0',
                 "batchId": "472351"}
    get_num = 100
    got_num = 0
        # 参数8要拿时间戳
    url_search = re.search("http[s]{0,1}://www.lofter.com/tag/(.*?)/(.*)", url)
    type = url_search.group(2)
    if type == "":
        type = "total"
    data_parme = {'c0-scriptName': 'TagBean',
                    'c0-methodName': 'search',
                    'c0-param0': 'string:' + url_search.group(1),
                    'c0-param1': 'number:0',
                    'c0-param2': 'string:',
                    'c0-param3': 'string:' + type,
                    'c0-param4': 'boolean:false',
                    'c0-param5': 'number:0',
                    'c0-param6': 'number:' + str(get_num),
                    'c0-param7': 'number:' + str(got_num),
                    'c0-param8': 'number:' + str(int(time.time() * 1000)),
                    'batchId': '870178'}
    data = {**base_data, **data_parme}
    return data

def update_data(data, get_num, got_num, last_timestamp="0"):
    """
    获取归档页时，每个请求都需要根据上次获取的内容更新data，才能成功获取到下一页的内容
    :param data:    原data
    :param get_num: 要获取的条数
    :param got_num: 已获取的条数
    :param last_timestamp:  tag模式需要上次获取的最后一条博客的发表时间戳作为参数
    :return:    更新后的data
    """
    if last_timestamp == "":
        print("tag模式更新data需要last_timestamp参数")
        return data
    data["c0-param6"] = 'number:' + str(get_num)
    data["c0-param7"] = 'number:' + str(got_num)
    data["c0-param8"] = 'number:' + str(last_timestamp)
    return data

def save_all_fav(url, file_path):
    # 获取所有博客信息，按条数切分

    # 各种设置，不同模式使用不用链接
    real_got_num = 0
    got_num = 0
    get_num = 100
    requests_url = "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"
    session = requests.session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.88 Safari/537.36",
        "Host": "www.lofter.com",
        "Referer": "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"
    }

    session.headers = headers
    data = make_data(url)

    fav_info = []

    # 开始获取归档页
    while True:
        print("正在获取{}-{}".format(got_num, got_num + get_num), end="\t")
        fav_response = session.post(requests_url, data=data)
        content = fav_response.content.decode("utf-8")
        # activityTags应该是第一或者第二个属性，从这切差不多能保证信息完整
        new_info = content.split("activityTags")[1:]
        fav_info += new_info
        got_num += get_num
        real_got_num += len(new_info)
        print("实际返回条数 {}".format(len(new_info)), end="\t")

        str1 = "tag页面"
        """
        调试中
        """

        # 长度为0说明已经到最后一页，或者被lofter发现了
        if len(new_info) == 0:
            print("\n已获取到最后一页，{}信息获取完成".format(str1))
            break

        last_hot = 0
        try:
            last_hot = int(re.search('s\d{1,5}.hot=(.*?);', new_info[-1]).group(1))
        except:
            pass
        print("最后一条热度为 {}".format(last_hot), end="")

        # 更新data
        last_info = new_info[-1]
        last_public_timestamp = re.search('s\d{1,5}.publishTime=(.*?);', last_info).group(1)
        data = update_data(data, get_num, got_num, last_public_timestamp)

    # 归档页出来了啥都没获取到
    if len(fav_info) == 0:
        print("归档页获取异常")
        exit()

    file = open(file_path + "/blogs_info", "w", encoding="utf-8")
    for info in fav_info:
        file.write(info.replace("\n", ""))
        file.write("\n\nsplit_line\n\n")
    print("总请求条数：{}  实际返回条数：{}".format(got_num, real_got_num))

def infor_formater(favs_info, file_path):
    # 把字段从原文件中提取出来，大部分使用正则
    format_fav_info = []

    for fav_info in favs_info:
        blog_info = {}
        # 博客链接
        try:
            url = re.search('s\d{1,5}.blogPageUrl="(.*?)"', fav_info).group(1)
        except:
            print("博客{} 信息丢失，跳过".format(favs_info.index(fav_info) + 1))
            continue
        blog_info["url"] = url
        # tags
        tags = re.search('s\d{1,5}.tag[s]{0,1}="(.*?)";', fav_info).group(1).strip().encode('utf-8').decode(
            'unicode_escape').split(",")
        if tags[0] == "":
            tags = []
        lower_tags = []
        for tag in tags:
            # 转小写，全角空格转半角
            lower_tag = tag.lower().replace(" ", " ").strip()
            lower_tags.append(lower_tag)
        blog_info["tags"] = lower_tags

        # 图片链接
        img_urls = []
        urls_search = re.search('originPhotoLinks="(\[.*?\])"', fav_info)
        if urls_search:
            urls_str = urls_search.group(1).replace("\\", "").replace("false", "False").replace("true", "True")
            urls_infos = eval(urls_str)
            for url_info in urls_infos:
                # raw是没有任何后缀的原图，但有的没有raw，取orign
                try:
                    url = url_info["raw"]
                except:
                    url = url_info["orign"].split("?imageView")[0]
                if "netease" in url:
                    url = url_info["orign"].split("?imageView")[0]
                img_urls.append(url)
        blog_info["img_urls"] = img_urls

        blog_info["is_push"] = "false"
        # 输出信息看看
        print(blog_info)

        # 整合后输出
        format_fav_info.append(blog_info)
        print("解析进度 {}/{}   正在解析的博客链接 {}".format(len(format_fav_info), len(favs_info), blog_info["url"]))

    # 写入到文件
    with open(file_path + "/format_blogs_info.json", "w", encoding="utf-8", errors="ignore") as op:
        op.write(json.dumps(format_fav_info, ensure_ascii=False, indent=4))

#获取一条用于推送的url
def get_img_urls(blogs_info, file_path):
    img_urls = []
    for blog_info in blogs_info:
        #遍历所有数据，每次取一条imgurl,取过的过滤
        if blog_info["is_push"] == "false":
            blog_info["is_push"] = "true"
            img_urls = blog_info["img_urls"]
            break
        else:
            continue
    # 写入到文件
    with open(file_path + "/format_blogs_info.json", "w", encoding="utf-8", errors="ignore") as op:
        op.write(json.dumps(blogs_info, ensure_ascii=False, indent=4))
    return img_urls

def post_robot(webhook, img_urls):
    headers = {
        'Content-Type: application/json',
    }
    for img_url in img_urls:
        data = {
            "msgtype": "message",
            "layouts": [{
                "type": "column_layout",
                "components": [{
                    "type": "image",
                    "url": str(img_url),
                    "width": "",
                    "height": "",
                    "aspect_ratio": "1.0",
                    "component_fit": "contain"
                }, {
                    "type": "plain_text",
                    "text": "按时间推送最新内容",
                    "style": "regular"
                }],
                "style": {
                    "vertical_line": ""
                }
            }]
        }
        resp = requests.post(webhook,json = data).json()
        print(resp)

def run(url, webhook, force_refresh, base_path):
    print(url)
    file_path = base_path
    tag_file_path = base_path + "/tag_file"
    #文件保存位置
    if url.split("/")[-1] not in ["new", "total", "month", "week", "date"]:
        url += "/total"
        print(url)
        tag = re.search("http[s]{0,1}://www.lofter.com/tag/(.*?)/.*", url).group(1)
        tag = parse.unquote(tag)
        file_path = tag_file_path + "/" + tag
    #不存在文件夹就new一个
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    step1_start_time = time.time()
    print("第一步，获取页面信息")
    #需要强制更新信息或者不存在页面信息就拉最新的
    if not os.path.exists(file_path + "/format_blogs_info.json") or force_refresh:
        save_all_fav(url, file_path)
        fav_str = open(file_path + "/blogs_info", "r", encoding="utf-8").read()
        fav_info = fav_str.split("\n\nsplit_line\n\n")
        fav_info = fav_info[0:-1]

        print("\n开始解析")

        infor_formater(fav_info, file_path)
        step1_finish_time = time.time()
        print("解析完成")
        print("阶段1耗时 {} 分钟".format(round((step1_finish_time - step1_start_time) / 60), 2))
    else:
        print("使用已经存在的页面信息")
    blogs_info = json.loads(open(file_path + "/format_blogs_info.json", encoding="utf-8").read())
    #     classified_info = {"img": [], "article": [], "long article": [], "text": []}
    # # 分类，有图片链接为图片类型，有长文内容为长文(长文也有标题，必须在文章前面)，有标题为文章，剩余的为文本
    # for blog_info in blogs_info:
    #     if blog_info["img urls"]:
    #         classified_info["img"].append(blog_info)
    # return classified_info

    #上一步里生成完了初始数据里，理论上已经够用了
    img_urls = get_img_urls(blogs_info, file_path)
    #获取到urls列表
    print(img_urls)
    #推送机器人
    post_robot(webhook, img_urls)

def main_handler(event, context):
    print("Received event: " + json.dumps(event, indent = 2)) 
    print("Received context: " + str(context))
    # 基础设置  -------------------------------------------------------- # 爬这个url下的图片推送到企业微信，后续做回调改url即可
    url = "https://www.lofter.com/tag/%E8%99%B9%E5%A4%8F/new"

    #企业微信机器人webhook
    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=cfc33bd3-1251-490f-a341-0985f00403bc'

    # 文件设置  -------------------------------------------------------- #
    # 运行中产生的文件和保存文件的存放路径
    file_path = "/tmp"

    force_refresh = 0

    # 主逻辑入口
    run(url, webhook, force_refresh, file_path)