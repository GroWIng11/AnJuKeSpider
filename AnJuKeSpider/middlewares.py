# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import datetime
import io
import random
import threading
import time
from urllib.parse import urlparse
from scrapy import signals
from PIL import Image
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class AnjukespiderSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AnjukespiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class CaptchaMiddleware:
    lock = threading.Lock()
    driver = None
    verified = False
    last_verify_time = datetime.datetime.now()

    def __init__(self, crawler):
        self.crawler = crawler
        self.driver = None
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        # service = Service(executable_path=r"D:\chromedriver-win64\chromedriver.exe")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式，可选
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)
        self.driver.set_page_load_timeout(10)

    def spider_closed(self, spider):
        if self.driver:
            self.driver.quit()

    def process_request(self, request, spider):
        if 'https://callback.58.com/antibot/verifycode' in request.url:
            with self.lock:
                spider.logger.info("开始处理验证码...")
                if not self.verified or (datetime.datetime.now() - self.last_verify_time).seconds > 60:
                    try:
                        self.handle_captcha(request, spider)
                        self.verified = True
                        self.last_verify_time = datetime.datetime.now()
                    except Exception as e:
                        spider.logger.error(f"处理验证码失败: {e}")
                else:
                    pass
            return scrapy.Request(request.meta['detail_page'], dont_filter=True, meta=request.meta)
        return None

    def handle_captcha(self, request, spider):
        try:
            self.driver.get(request.url)
            btn = self.driver.find_element(By.ID, 'btnSubmit')
            actions = ActionChains(self.driver)
            actions.move_to_element(btn).pause(0.5).click().perform()
        except Exception as e:
            spider.logger.error(f"获取按钮验证码失败: {e}")
            raise

        try:
            WebDriverWait(self.driver, 5).until(lambda d: 'anjuke.com' in urlparse(d.current_url).netloc)
            return
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: 'geetest_canvas_bg' in d.page_source and 
                'geetest_canvas_fullbg' in d.page_source and 
                'geetest_slider_button' in d.page_source)
        except Exception as e:
            spider.logger.error(f"获取滑动拼图验证码失败: {e}")
            raise

        try:
            image_bg, image_fullbg = self.capture_canvas_image(spider)
            offset = self.calculate_offset(image_bg, image_fullbg)
            element = self.driver.find_element(By.CLASS_NAME, "geetest_slider_button")
            ActionChains(self.driver).click_and_hold(on_element=element).perform()
            for x, y, t in [[offset, 0.5, 1]]:
                ActionChains(self.driver).move_to_element_with_offset(
                    to_element=element,
                    xoffset=x,
                    yoffset=y + 22).perform()
                ActionChains(self.driver).click_and_hold().perform()
                time.sleep(t)
            time.sleep(0.24)
            ActionChains(self.driver).release(on_element=element).perform()
            time.sleep(0.8)
        except Exception as e:
            spider.logger.error(f"解析滑动拼图验证码失败: {e}")
            raise

        try:
            WebDriverWait(self.driver, 10).until(lambda d: 'anjuke.com' in urlparse(d.current_url).netloc)
            return
        except Exception as e:
            spider.logger.error(f"最终未跳转至安居客详情页: {e}")
            raise

    def compare_pixel(self, pix1, pix2, x, y):
        """像素对比, (R, G, B, A) ，判断像素差异是否过大"""
        diff_max = 50
        diff_r = abs(pix1[x, y][0] - pix2[x, y][0])
        diff_g = abs(pix1[x, y][1] - pix2[x, y][1])
        diff_b = abs(pix1[x, y][2] - pix2[x, y][2])
        return diff_r > diff_max and diff_g > diff_max and diff_b > diff_max


    def calculate_offset(self,img1: Image, img2: Image):
        """计算偏移量"""
        pix1 = img1.load()
        pix2 = img2.load()
        idx_x = []
        for x in range(img1.size[0]):
            for y in range(img1.size[1]):
                if self.compare_pixel(pix1, pix2, x, y):
                    idx_x.append(x)
        return sorted(idx_x)[0] - 3

    def capture_canvas_image(self, spider):
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
            canvas_bg_base64 = self.driver.execute_script(script_bg)
            canvas_fullbg_base64 =  self.driver.execute_script(script_bgfull)
            # 解码并保存图片
            import base64
            image_data_bg = base64.b64decode(canvas_bg_base64[22:])
            image_data_fullbg = base64.b64decode(canvas_fullbg_base64[22:])
            return Image.open(io.BytesIO(image_data_bg)), Image.open(io.BytesIO(image_data_fullbg))
        except Exception as e:
            spider.logger.error(f"捕获Canvas图片失败: {e}")
            return None

class ProxyMiddleware:
    proxies = [
        "http://d1537836213:qnr6v85h@61.184.8.27:21645",
        "http://d1537836213:qnr6v85h@61.184.8.27:21354",
        "http://d1537836213:qnr6v85h@58.19.54.132:20677",
        "http://d1537836213:qnr6v85h@58.19.54.132:20897",
        "http://d1537836213:qnr6v85h@218.95.37.135:21472",
        "http://d1537836213:qnr6v85h@218.95.37.135:20625",
        "http://d1537836213:qnr6v85h@58.19.54.132:21583",
        "http://d1537836213:qnr6v85h@116.208.196.81:20881",
        "http://d1537836213:qnr6v85h@218.95.37.135:20036",
        "http://d1537836213:qnr6v85h@36.151.192.211:25206",
        "http://d1537836213:qnr6v85h@171.41.151.3:16788",
        "http://d1537836213:qnr6v85h@182.106.136.217:21280",
        "http://d1537836213:qnr6v85h@36.25.243.10:20271",
        "http://d1537836213:qnr6v85h@218.95.37.135:20100",
        "http://d1537836213:qnr6v85h@218.95.37.11:25245",
        "http://d1537836213:qnr6v85h@36.25.243.10:20954",
        "http://d1537836213:qnr6v85h@182.106.136.217:20002",
        "http://d1537836213:qnr6v85h@218.95.37.11:25160",
        "http://d1537836213:qnr6v85h@218.95.37.135:20772",
        "http://d1537836213:qnr6v85h@221.229.212.173:25144",
        "http://d1537836213:qnr6v85h@36.25.243.10:21551",
        "http://d1537836213:qnr6v85h@218.95.37.135:21531",
        "http://d1537836213:qnr6v85h@61.184.8.27:20491",
        "http://d1537836213:qnr6v85h@58.19.54.132:21090",
        "http://d1537836213:qnr6v85h@218.95.37.11:25137",
        "http://d1537836213:qnr6v85h@36.25.243.10:21186",
        "http://d1537836213:qnr6v85h@58.19.54.132:21240",
        "http://d1537836213:qnr6v85h@116.208.197.79:21316",
        "http://d1537836213:qnr6v85h@218.95.37.135:20601",
        "http://d1537836213:qnr6v85h@221.229.212.173:25114",
        "http://d1537836213:qnr6v85h@36.25.243.10:20959",
        "http://d1537836213:qnr6v85h@218.95.37.251:25094",
        "http://d1537836213:qnr6v85h@218.95.37.135:20770",
        "http://d1537836213:qnr6v85h@218.95.37.135:21728",
        "http://d1537836213:qnr6v85h@119.102.156.167:18868",
        "http://d1537836213:qnr6v85h@182.106.136.217:20765",
        "http://d1537836213:qnr6v85h@58.19.54.132:20363",
        "http://d1537836213:qnr6v85h@58.19.55.10:28408",
        "http://d1537836213:qnr6v85h@36.25.243.10:20311",
        "http://d1537836213:qnr6v85h@218.95.37.135:21044",
        "http://d1537836213:qnr6v85h@180.103.220.246:21133",
        "http://d1537836213:qnr6v85h@218.95.37.135:21434",
        "http://d1537836213:qnr6v85h@120.41.150.91:20930",
        "http://d1537836213:qnr6v85h@221.234.28.229:18178",
        "http://d1537836213:qnr6v85h@182.106.136.217:20444",
        "http://d1537836213:qnr6v85h@117.30.222.98:18665",
        "http://d1537836213:qnr6v85h@58.19.54.6:25439",
        "http://d1537836213:qnr6v85h@36.25.243.10:20094",
        "http://d1537836213:qnr6v85h@61.184.8.27:21733",
        "http://d1537836213:qnr6v85h@182.106.136.217:20655",
        "http://d1537836213:qnr6v85h@58.19.54.132:20402",
        "http://d1537836213:qnr6v85h@218.95.37.135:20897"
    ]

    def process_request(self, request, spider):
        proxy = random.choice(self.proxies)
        request.meta['proxy'] = proxy  
        spider.logger.info(f"Using proxy {proxy}")

#处理验证码失败: can only concatenate str (not "TypeError") to str