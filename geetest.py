# -*-coding:utf-8-*-
import io
import json
import sys
from urllib.parse import urlparse
import requests
import re
# import StringIO
from PIL import Image
import random
import math
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from bs4 import BeautifulSoup


# class crack_picture(object):
#     def __init__(self, img_url1, img_url2):
#         self.img1, self.img2 = self.picture_get(img_url1, img_url2)

#     def picture_get(self, img_url1, img_url2):
#         hd = {"Host": "static.geetest.com",
#               "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
#         img1 = StringIO.StringIO(self.repeat(img_url1, hd).content)
#         img2 = StringIO.StringIO(self.repeat(img_url2, hd).content)
#         return img1, img2

#     def repeat(self, url, hd):
#         times = 10
#         while times > 0:
#             try:
#                 ans = requests.get(url, headers=hd)
#                 return ans
#             except:
#                 times -= 1

#     def pictures_recover(self):
#         xpos = self.judge(self.picture_recover(self.img1, 'img1.jpg'), self.picture_recover(self.img2, 'img2.jpg')) - 6
#         return self.darbra_track(xpos)

#     def picture_recover(self, img, name):
#         a = [39, 38, 48, 49, 41, 40, 46, 47, 35, 34, 50, 51, 33, 32, 28, 29, 27, 26, 36, 37, 31, 30, 44, 45, 43, 42, 12,
#              13, 23, 22, 14, 15, 21, 20, 8, 9, 25, 24, 6, 7, 3, 2, 0, 1, 11, 10, 4, 5, 19, 18, 16, 17]
#         im = Image.open(img)
#         im_new = Image.new("RGB", (260, 116))
#         for row in range(2):
#             for column in range(26):
#                 right = a[row * 26 + column] % 26 * 12 + 1
#                 down = 58 if a[row * 26 + column] > 25 else 0
#                 for w in range(10):
#                     for h in range(58):
#                         ht = 58 * row + h
#                         wd = 10 * column + w
#                         im_new.putpixel((wd, ht), im.getpixel((w + right, h + down)))
#         im_new.save(name)
#         return im_new

#     def darbra_track(self, distance):
#         return [[distance, 0.5, 1]]

#     def diff(self, img1, img2, wd, ht):
#         rgb1 = img1.getpixel((wd, ht))
#         rgb2 = img2.getpixel((wd, ht))
#         tmp = reduce(lambda x, y: x + y, map(lambda x: abs(x[0] - x[1]), zip(rgb1, rgb2)))
#         return True if tmp >= 200 else False

#     def col(self, img1, img2, cl):
#         for i in range(img2.size[1]):
#             if self.diff(img1, img2, cl, i):
#                 return True
#         return False

#     def judge(self, img1, img2):
#         for i in range(img2.size[0]):
#             if self.col(img1, img2, i):
#                 return i
#         return -1

# class gsxt(object):
#     def __init__(self, br_name="phantomjs"):
#         self.br = self.get_webdriver(br_name)
#         self.wait = WebDriverWait(self.br, 10, 1.0)
#         self.br.set_page_load_timeout(8)
#         self.br.set_script_timeout(8)

#     def input_params(self, name):
#         self.br.get("http://www.gsxt.gov.cn/index")
#         element = self.wait_for(By.ID, "keyword")
#         element.send_keys(name)
#         time.sleep(1.1)
#         element = self.wait_for(By.ID, "btn_query")
#         element.click()
#         time.sleep(1.1)

#     def drag_pic(self):
#         return (self.find_img_url(self.wait_for(By.CLASS_NAME, "gt_cut_fullbg_slice")),
#                 self.find_img_url(self.wait_for(By.CLASS_NAME, "gt_cut_bg_slice")))

#     def wait_for(self, by1, by2):
#         return self.wait.until(EC.presence_of_element_located((by1, by2)))

#     def find_img_url(self, element):
#         try:
#             return re.findall('url\("(.*?)"\)', element.get_attribute('style'))[0].replace("webp", "jpg")
#         except:
#             return re.findall('url\((.*?)\)', element.get_attribute('style'))[0].replace("webp", "jpg")

#     def emulate_track(self, tracks):
#         element = self.br.find_element_by_class_name("gt_slider_knob")
#         ActionChains(self.br).click_and_hold(on_element=element).perform()
#         for x, y, t in tracks:
#             ActionChains(self.br).move_to_element_with_offset(
#                 to_element=element,
#                 xoffset=x + 22,
#                 yoffset=y + 22).perform()
#             ActionChains(self.br).click_and_hold().perform()
#             time.sleep(t)
#         time.sleep(0.24)
#         ActionChains(self.br).release(on_element=element).perform()
#         time.sleep(0.8)
#         element = self.wait_for(By.CLASS_NAME, "gt_info_text")
#         ans = element.text
#         print ans
#         return ans

#     def run(self):
#         for i in [u'招商银行', u'交通银行', u'中国银行']:
#             self.hack_geetest(i)
#             time.sleep(1)
#         self.quit_webdriver()

#     def hack_geetest(self, company=u"招商银行"):
#         flag = True
#         self.input_params(company)
#         while flag:
#             img_url1, img_url2 = self.drag_pic()
#             tracks = crack_picture(img_url1, img_url2).pictures_recover()
#             tsb = self.emulate_track(tracks)
#             if u'通过' in tsb:
#                 time.sleep(1)
#                 soup = BeautifulSoup(self.br.page_source, 'html.parser')
#                 for sp in soup.find_all("a", attrs={"class": "search_list_item"}):
#                     print re.sub("\s+", "", sp.get_text().encode("utf-8"))
#                 break
#             elif u'吃' in tsb:
#                 time.sleep(5)
#             else:
#                 self.input_params(company)

#     def quit_webdriver(self):
#         self.br.quit()

#     def get_webdriver(self, name):
#         if name.lower() == "phantomjs":
#             dcap = dict(DesiredCapabilities.PHANTOMJS)
#             dcap["phantomjs.page.settings.userAgent"] = (
#                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36")
#             return webdriver.PhantomJS(desired_capabilities=dcap)
#         elif name.lower() == "chrome":
#             return webdriver.Chrome()

def compare_pixel(pix1, pix2, x, y):
    """像素对比, (R, G, B, A) ，判断像素差异是否过大"""
    diff_max = 50
    diff_r = abs(pix1[x, y][0] - pix2[x, y][0])
    diff_g = abs(pix1[x, y][1] - pix2[x, y][1])
    diff_b = abs(pix1[x, y][2] - pix2[x, y][2])
    return diff_r > diff_max and diff_g > diff_max and diff_b > diff_max


def calculate_offset(img1: Image, img2: Image):
    """计算偏移量"""
    pix1 = img1.load()
    pix2 = img2.load()
    idx_x = []
    for x in range(img1.size[0]):
        for y in range(img1.size[1]):
            if compare_pixel(pix1, pix2, x, y):
                idx_x.append(x)
    return sorted(idx_x)[0] - 3

def capture_canvas_image(driver):
    """从Canvas元素捕获图片"""
    try:
        # 执行JavaScript获取Canvas数据
        script_bg = f"""
            var canvas = document.getElementsByClassName('geetest_canvas_bg');
            return canvas[0].toDataURL();
        """
        
        script_bgfull = f"""
            var canvas = document.getElementsByClassName('geetest_canvas_fullbg');
            return canvas[0].toDataURL();
        """

        # 获取Base64编码的图片数据
        canvas_bg_base64 = driver.execute_script(script_bg)
        canvas_fullbg_base64 = driver.execute_script(script_bgfull)
        # 解码并保存图片
        import base64
        image_data_bg = base64.b64decode(canvas_bg_base64[22:])
        image_data_fullbg = base64.b64decode(canvas_fullbg_base64[22:])

        filename_bg = f"canvas_bg.webp"
        filename_fullbg = f"canvas_fullbg.webp"
        
        with open(filename_bg, 'wb') as f:
            f.write(image_data_bg)
        with open(filename_fullbg, "wb") as f:
            f.write(image_data_fullbg)

        return Image.open(io.BytesIO(image_data_bg)), Image.open(io.BytesIO(image_data_fullbg))

    except Exception as e:
        print(f"捕获Canvas图片失败: {e}")
        return None


def geetest(driver, url):


    try:
        driver.get(url)
        btn = driver.find_element(By.ID, 'btnSubmit')
        actions = ActionChains(driver)
        actions.move_to_element(btn).pause(0.5).click().perform()
    except Exception as e:
        print("点击验证按钮失败")
        return

    try:
        WebDriverWait(driver, 10).until(lambda d: 'anjuke.com' in urlparse(d.current_url).netloc)
        print("验证完成，已跳转至安居客详情页")
        return
    except Exception as e:
        pass

    try:
        WebDriverWait(driver, 10).until(
            lambda d: 'geetest_canvas_bg' in d.page_source and 
            'geetest_canvas_fullbg' in d.page_source and 
            'geetest_slider_button' in d.page_source)

        print("验证中，已获取滑动拼图验证码")
        image_bg, image_fullbg = capture_canvas_image(driver)
        offset = calculate_offset(image_bg, image_fullbg)
        print(f"offset: {offset}")

        element = driver.find_element(By.CLASS_NAME, "geetest_slider_button")
        ActionChains(driver).click_and_hold(on_element=element).perform()
        for x, y, t in [[offset, 0.5, 1]]:
            ActionChains(driver).move_to_element_with_offset(
                to_element=element,
                xoffset=x,
                yoffset=y + 22).perform()
            ActionChains(driver).click_and_hold().perform()
            time.sleep(t)
        time.sleep(0.24)
        ActionChains(driver).release(on_element=element).perform()
        time.sleep(0.8)
    except Exception as e:
        print("滑动拼图验证失败")
        pass

    try:
        WebDriverWait(driver, 10).until(lambda d: 'anjuke.com' in urlparse(d.current_url).netloc)
        print("验证完成，已跳转至安居客详情页")
        return
    except Exception as e:
        print("验证失败")
        pass


if __name__ == "__main__":
    service = Service(executable_path=r"D:\chromedriver-win64\chromedriver.exe")
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5.0)

    geetest(driver, sys.argv[1])

    driver.quit()
    