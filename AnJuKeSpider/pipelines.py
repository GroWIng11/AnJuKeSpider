# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime
import logging
from itemadapter import ItemAdapter
import pymysql

from AnJuKeSpider.items import RentalItem


class AnjukespiderPipeline:
    def process_item(self, item, spider):
        return item

class MySQLPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
        self.batch_size = 50  # 批量处理大小
        self.batch_count = 0
        self.batch_items = []

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = {
            'db': crawler.settings.get('MYSQL_DB'),
            'user': crawler.settings.get('MYSQL_USER'),
            'password': crawler.settings.get('MYSQL_PASSWORD'),
            'host': crawler.settings.get('MYSQL_HOST'),
            'port': crawler.settings.get('MYSQL_PORT'),
            'charset': crawler.settings.get('MYSQL_CHARSET', 'utf8mb4'),
            'use_unicode': crawler.settings.get('MYSQL_USE_UNICODE', True),
        }
        return cls(db_settings)
    
    def open_spider(self, spider):
        try:
            self.conn = pymysql.connect(
                db=self.db_settings['db'],
                user=self.db_settings['user'],
                password=self.db_settings['password'],
                host=self.db_settings['host'],
                port=self.db_settings['port'],
                charset=self.db_settings['charset'],
                use_unicode=self.db_settings['use_unicode'],
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            self._create_tables()
            self.logger.info("Connected to MySQL database")
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise

    def close_spider(self, spider):
        # 处理剩余的批次
        if self.batch_items:
            self._process_batch()
            
        # 标记不活跃的记录
        self._mark_inactive('安居客')
        
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("Database connection closed")

    def _create_tables(self):
        # 创建主表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source_id VARCHAR(50) NOT NULL,
                source VARCHAR(20) NOT NULL,
                url TEXT NOT NULL,
                crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_update_time DATETIME,
                
                title TEXT NOT NULL,
                description TEXT,
                type VARCHAR(20),
                bedrooms SMALLINT DEFAULT 0,
                livingrooms SMALLINT DEFAULT 0,
                bathrooms SMALLINT DEFAULT 0,
                area FLOAT DEFAULT 0,
                orientation VARCHAR(10),
                decoration VARCHAR(20),

                address TEXT,
                
                price DECIMAL(10, 2) DEFAULT 0,
                deposit VARCHAR(50),
                
                floor VARCHAR(50),
                total_floor VARCHAR(50),
                facilities JSON,
                
                image_urls JSON,
                
                is_active TINYINT(1) DEFAULT 1,
                
                UNIQUE KEY unique_source_listing (source, source_id),
                INDEX idx_source_active (source, is_active),
                INDEX idx_price (price)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # 创建价格历史表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                listing_id INT,
                recorded_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                price DECIMAL(10, 2),
                INDEX idx_listing_id (listing_id),
                FOREIGN KEY (listing_id) 
                    REFERENCES listings(id) 
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        self.conn.commit()

    def process_item(self, item, spider):
        # 只处理RentalItem类型
        if not isinstance(item, RentalItem):
            return item
            
        adapter = ItemAdapter(item)
        
        # 设置默认值
        if 'crawl_time' not in adapter or not adapter['crawl_time']:
            adapter['crawl_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加到批处理
        self.batch_items.append(dict(adapter))
        self.batch_count += 1
        
        # 达到批处理大小
        if self.batch_count >= self.batch_size:
            self._process_batch()
            
        return item
    
    def _process_batch(self):
        if not self.batch_items:
            return
            
        try:
            # 批量插入或更新
            for item in self.batch_items:
                self._upsert_listing(item)
                
            self.conn.commit()
            # self.logger.info(f"Processed batch of {len(self.batch_items)} items")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Batch processing error: {e}")
            # 单个处理回退
            for item in self.batch_items:
                try:
                    self._upsert_listing(item)
                    self.conn.commit()
                except Exception as single_e:
                    self.conn.rollback()
                    self.logger.error(f"Error processing item {item.get('source_id')}: {single_e}")
        
        # 重置批次
        self.batch_items = []
        self.batch_count = 0

    def _upsert_listing(self, item):
        # 检查记录是否存在
        self.cursor.execute(
            "SELECT id, price FROM listings WHERE source = %s AND source_id = %s",
            (item['source'], item['source_id'])
        )
        existing = self.cursor.fetchone()

        if existing:
            # 更新现有记录
            listing_id, old_price = existing['id'], existing['price']
            self._update_listing(item, listing_id)
            
            # 如果价格变化，记录到历史表
            if 'price' in item and item['price'] != old_price and item['price'] is not None and item['price'] > 0:
                self._record_price_change(listing_id, item['price'])
        else:
            # 插入新记录
            self._insert_listing(item)

    def _insert_listing(self, item):
        insert_sql = """
            INSERT INTO listings (
                source_id, source, url, 
                crawl_time, last_update_time,
                title, description, type, bedrooms, livingrooms, bathrooms, area, orientation, decoration,
                address,
                price, deposit,
                floor, total_floor,  facilities,
                image_urls
            ) VALUES (
                %(source_id)s, %(source)s, %(url)s, 
                %(crawl_time)s, %(last_update_time)s,
                %(title)s, %(description)s, %(type)s, %(bedrooms)s, %(livingrooms)s, %(bathrooms)s, 
                %(area)s, %(orientation)s, %(decoration)s,
                %(address)s,
                %(price)s, %(deposit)s,
                %(floor)s, %(total_floor)s, JSON_ARRAY%(facilities)s,
                JSON_ARRAY%(image_urls)s
            )
        """

        self.cursor.execute(insert_sql, item)
        listing_id = self.cursor.lastrowid
        # self.logger.info(f"Inserted new listing: {item['source']}-{item['source_id']} (ID: {listing_id})")
        return listing_id
    
    def _update_listing(self, item, listing_id):
        update_sql = """
            UPDATE listings SET
                url = %(url)s,
                last_update_time = %(last_update_time)s,
                title = %(title)s,
                description = %(description)s,
                type = %(type)s,
                bedrooms = %(bedrooms)s,
                livingrooms = %(livingrooms)s,
                bathrooms = %(bathrooms)s,
                area = %(area)s,
                orientation = %(orientation)s,
                decoration = %(decoration)s,
                address = %(address)s,
                price = %(price)s,
                deposit = %(deposit)s,
                floor = %(floor)s,
                total_floor = %(total_floor)s,
                facilities = JSON_ARRAY%(facilities)s,
                image_urls = JSON_ARRAY%(image_urls)s,
                is_active = 1
            WHERE id = %(listing_id)s
        """
        
        params = dict(item)
        params['listing_id'] = listing_id
        
        if 'last_update_time' not in params or not params['last_update_time']:
            params['last_update_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(update_sql, params)
        # self.logger.info(f"Updated listing: {item['source']}-{item['source_id']} (ID: {listing_id})")

    def _record_price_change(self, listing_id, new_price):
        insert_sql = """
            INSERT INTO price_history (listing_id, price)
            VALUES (%s, %s)
        """
        self.cursor.execute(insert_sql, (listing_id, new_price))
        # self.logger.info(f"Recorded price change for listing {listing_id}: {new_price}")

    def _mark_inactive(self, source):
        # 在爬虫结束时调用，标记未更新的记录为不活跃
        try:
            self.cursor.execute("""
                UPDATE listings 
                SET is_active = 0 
                WHERE source = %s 
                AND last_update_time < NOW() - INTERVAL 3 DAY
                AND is_active = 1
            """, (source,))
            self.conn.commit()
            inactive_count = self.cursor.rowcount
            self.logger.info(f"Marked {inactive_count} listings as inactive for source: {source}")
        except Exception as e:
            self.logger.error(f"Error marking inactive listings: {e}")
            self.conn.rollback()