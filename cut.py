# coding: utf8
# 安装依赖：numpy, pandas, Pillow, request
from bs4 import BeautifulSoup as bs
from PIL import Image
from io import BytesIO
import os
import requests
import numpy as np
import base64

np.set_printoptions(threshold=np.inf)


# 将图片转化为模型
def get_modes(imgs):
    modes = []
    for img in imgs:
        mode = np.asarray(img)
        mode = np.where(mode < 120, 0, 1)
        modes.append(mode)
    return modes


# 破解前端js加密
def trans_id(username, password):
    user = str(base64.b64encode(
        bytes(username, encoding='utf8')), encoding='utf8')
    pwd = str(base64.b64encode(
        bytes(password, encoding='utf8')), encoding='utf8')

    result = '{}%%%{}'.format(user, pwd)
    return result


# 识别验证码
def get_captcha(img):
    # 导入模型名称
    def get_fname():
        name_list = []
        path = 'mode/'
        dirs = os.listdir(path)
        for dir_ in dirs:
            name_list.append(dir_)
        return name_list
    # 灰度化 切割 转化为数组模型
    img = img.convert('L')
    box1 = (4, 4, 12, 16)
    box2 = (14, 4, 22, 16)
    box3 = (24, 4, 32, 16)
    box4 = (34, 4, 42, 16)
    img1 = img.crop(box1)
    img2 = img.crop(box2)
    img3 = img.crop(box3)
    img4 = img.crop(box4)
    imgs = [img1, img2, img3, img4]
    modes = get_modes(imgs)
    # print(modes[1])
    # print(modes[3])
    # np.save('mode/n.npy',modes[1])
    # np.save('mode/m1.npy',modes[3])
    name_list = get_fname()
    last_num = ''
    # 分别计算验证码中4个模型的最小欧拉距离的值
    for mode in modes:
        disk_log = {}
        for name in name_list:
            npdata = np.load('mode/{}'.format(name))
            dist = np.linalg.norm(npdata - mode)
            disk_log[name] = dist
        last_num = last_num + min(disk_log, key=disk_log.get)[0]
    return last_num


def get_table(username, password):
    url = 'http://jwc104.ncu.edu.cn:8081/jsxsd/verifycode.servlet'
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    }
    response = session.get(url, headers=headers)
    img = Image.open(BytesIO(response.content))
    # img.show()
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    cookies = 'JSESSIONID={};SERVERID={}'.format(
        cookies['JSESSIONID'], cookies['SERVERID'])
    post_url = 'http://jwc104.ncu.edu.cn:8081/jsxsd/xk/LoginToXk'
    headers['Cookie'] = cookies

    user = trans_id(str(username), str(password))
    captcha = get_captcha(img)
    print(captcha)
    data = {
        'encoded': user,
        'RANDOMCODE': captcha
    }
    res = session.post(post_url, headers=headers, data=data)
    if '验证码错误' in res.text:
        print('验证码错误')
        return '验证码错误'
    elif '密码错误' in res.text:
        print('用户名或密码错误')
        return '用户名或密码错误'
    else:
        url_kb = 'http://jwc104.ncu.edu.cn:8081/jsxsd/xskb/xskb_list.do'

        html = session.get(url_kb, headers=headers).text

        soup = bs(html, 'lxml')
        table = soup.find_all('table')[-1]

        tr_lst = table.find_all('tr')
        columns, data = tr_lst[0], tr_lst[1:-1]
        return data

# 测试识别率 2次都是78%


if __name__ == '__main__':
    res = get_table('usernamer', 'password')
