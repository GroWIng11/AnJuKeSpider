# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from copy import deepcopy
import re
from itemloaders import ItemLoader
import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join, Identity

def clean_text(text):
    """清理文本中的多余空格和换行"""
    if text:
        return re.sub(r'\s+', ' ', text).strip()
    return text

def parse_float(value):
    """解析浮点数"""
    try:
        return float(re.sub(r'[^\d.]', '', value))
    except:
        return None

def parse_int(value):
    """解析整数"""
    try:
        return int(re.sub(r'[^\d]', '', value))
    except:
        return None

def parse_bool(value):
    """解析布尔值"""
    if isinstance(value, bool):
        return value
    lower_val = str(value).lower()
    return lower_val in ['true', 'yes', '1', '包含', '是', '有']

class RentalItem(scrapy.Item):
    # define the fields for your item here like:
    source_id = scrapy.Field(default='')
    url = scrapy.Field(default='')
    source = scrapy.Field(default='安居客')
    crawl_time = scrapy.Field(default='')
    last_update_time = scrapy.Field(default='')
    title = scrapy.Field(default='')

    description = scrapy.Field(
        default='',
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )
    requirements = scrapy.Field(
        default='',
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )

    bedrooms = scrapy.Field(
        default='0',
        input_processor=MapCompose(parse_int),
        output_processor=TakeFirst()
    )
    livingrooms = scrapy.Field(
        default='0',
        input_processor=MapCompose(parse_int),
        output_processor=TakeFirst()
    )
    bathrooms = scrapy.Field(
        default='0',
        input_processor=MapCompose(parse_int),
        output_processor=TakeFirst()
    )

    area = scrapy.Field(
        default='0',
        input_processor=MapCompose(parse_float),
        output_processor=TakeFirst()
    )
    orientation = scrapy.Field(default='')
    decoration = scrapy.Field(default='')
    # district = scrapy.Field()
    type = scrapy.Field(default='')
    # subdistrict = scrapy.Field()
    # neighborhood = scrapy.Field()
    address = scrapy.Field(default='')

    price = scrapy.Field(
        default='0',
        input_processor=MapCompose(parse_float),
        output_processor=TakeFirst()
    )
    deposit = scrapy.Field(default='')
    # mangagement_fee = scrapy.Field()
    floor = scrapy.Field(default='')
    total_floor = scrapy.Field(default='')
    # furnishing = scrapy.Field()
    facilities = scrapy.Field(
        default=[],
        output_processor=Identity()
    )
    # building_facilities = scrapy.Field()
    lister_type = scrapy.Field()
    lister_name = scrapy.Field()
    lister_contact = scrapy.Field()
    image_urls = scrapy.Field(
        default=[],
        output_processor=Identity()
    )
    images = scrapy.Field()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        
    #     # 确保所有字段都存在，即使没有赋值
    #     for field_name, field_meta in self.fields.items():
    #         if field_name not in self:
    #             default_value = field_meta.get('default')
    #             # 处理可调用默认值（如list、dict等）
    #             if callable(default_value) and not isinstance(default_value, (str, int, float, bool)):
    #                 self[field_name] = default_value()
    #             else:
    #                 self[field_name] = deepcopy(default_value)

class RentalItemLoader(ItemLoader):
    default_item_class = RentalItem
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    def load_item(self):
        item = super().load_item()
        
        # 确保所有字段都存在
        for field_name, field_meta in self.item.fields.items():
            if field_name not in item:
                default_value = field_meta.get('default')
                # 处理可调用默认值（如list、dict等）
                if callable(default_value) and not isinstance(default_value, (str, int, float, bool)):
                    self.item[field_name] = default_value()
                else:
                    self.item[field_name] = deepcopy(default_value)
        
        return item