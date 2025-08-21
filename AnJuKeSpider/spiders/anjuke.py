import datetime
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from itemloaders import ItemLoader
import scrapy

from AnJuKeSpider.items import RentalItem, RentalItemLoader


class AnjukeSpider(scrapy.Spider):
    name = "anjuke"
    allowed_domains = ["anjuke.com"]
    start_urls = ["https://sg.zu.anjuke.com/fangyuan/"]
    KEEP_PARAMS = {"isauction", "shangquan_id", "psid"}

    def parse(self, response):
        yield from self.parse_list_page(response)

    def parse_list_page(self, response):
        for i, link in enumerate(response.xpath('//div[contains(@class, "zu-itemmod")]/@link').getall()):
            link = response.urljoin(link)
            parsed = urlparse(link)
            params = parse_qs(parsed.query)
            filter_params = {k : v for k, v in params.items() if k in self.KEEP_PARAMS}
            if 'isauction' in filter_params:
                filter_params['isauction'] = '1'
            new_query = urlencode(filter_params, doseq=True)
            link = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            yield response.follow(link, callback=self.parse_detail_page, dont_filter=True, meta={'detail_page': link})
        next_page = response.xpath('//a[contains(@class, "aNxt")]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_list_page)

    def parse_detail_page(self, response):
        loader = RentalItemLoader(item=RentalItem(), response=response, selector=response.selector)

        loader.add_value('source', '安居客')
        loader.add_value('source_id', response.url.split('/')[-1].split('?')[0])
        loader.add_value('title', response.xpath('.//h1[@class="house-title"]/div[contains(@class,"tit-rest")]/text()').get())
        loader.add_value('url', response.url)

        house_info = response.xpath('.//ul[contains(@class, "house-info-zufang")]')
        if house_info is not None:
            loader.add_value
            loader.add_value('price', ''.join(house_info.xpath('.//span[@class="price"]/.//text()').getall()))
            loader.add_value('deposit', house_info.xpath('.//span[@class="type"]/text()').get())
            for house_info_item in house_info.xpath('./li[@class="house-info-item"]'):
                item_info = ''.join(house_info_item.xpath('.//text()').getall()).replace('\n', '').replace(' ','')
                if '户型：' in item_info:
                    nums = 0
                    for c in item_info.replace('户型：', ''):
                        if c.isdigit():
                            nums = c
                        elif c == '室':
                            loader.add_value('bedrooms', nums)
                        elif c == '厅':
                            loader.add_value('livingrooms', nums)
                        elif c == '卫':
                            loader.add_value('bathrooms', nums)
                elif '面积：' in item_info:
                    loader.add_value('area', item_info)
                elif '朝向：' in item_info:
                    loader.add_value('orientation', item_info)
                elif '楼层：' in item_info:
                    loader.add_value('floor', item_info)
                    infos =item_info.replace('楼层：', '').split('共')
                    if len(infos) >= 2:
                        loader.add_value('total_floor', infos[1].replace(')', ''))
                elif '装修' in item_info:
                    loader.add_value('decoration', item_info.replace('装修：', ''))
                elif '地址：' in item_info:
                    loader.add_value('address', item_info.replace('地址：', ''))
                elif '小区：' in item_info:
                    loader.add_value('address', item_info.replace('小区：', ''))
                elif '类型' in item_info:
                    loader.add_value('type', item_info)


        house_info_peitao = response.xpath('.//ul[contains(@class, "house-info-peitao")]')
        if house_info_peitao is not None:
            loader.add_value('facilities', [''.join(peitao_item.xpath('.//text()').getall()).replace('\n', '').replace(' ','') for peitao_item in house_info_peitao.xpath('./li[contains(@class, "peitao-item") and contains(@class, "has")]')])
        else:
            loader.add_value('facilities', [])
        for mod_title in response.xpath('.//div[@class="lbox"]/div[contains(@class, "mod-title") and contains(@class, "bottomed")]'):
            h2 = mod_title.xpath('./h2/text()').get()
            if h2 == '房源概况' or h2 == '房源详情':
                loader.add_value('description', '\n'.join(mod_title.xpath('./following-sibling::div[1]/.//text()').getall()).replace('\n', '').replace(' ',''))
            elif h2 == '出租要求':
                loader.add_value('requirements', '\n'.join(mod_title.xpath('./following-sibling::div[1]/.//text()').getall()).replace('\n', '').replace(' ',''))

        loader.add_value('image_urls', response.xpath('//img/@data-src').getall())
        loader.add_value('last_update_time', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        self.logger.info(f"完成解析详情页 {response.url}")

        yield loader.load_item()