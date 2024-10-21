# Correct Data
数据结构说明：
users: 包含用户的信息，如用户 ID、用户名、邮箱、密码、创建时间和账号状态。
products: 包含产品信息，包括产品 ID、名称、类别、价格、库存量和创建时间。
orders: 包含订单信息，包括订单 ID、用户 ID、订单日期、总金额、状态和包含的产品列表（每个产品的 ID、数量和价格）。
reviews: 包含用户对产品的评价，包括评价 ID、产品 ID、用户 ID、评分、评论内容和创建时间。
inventory: 包含库存信息，包括产品 ID、当前库存量和上次更新库存的时间。

# Error Data
错误类型说明：
users:

user_id: 本应是整数，但给出了字符串 "one"。
username: 本应是字符串，但给出了整数 12345。
email: 本应是字符串（有效的电子邮件），但给出了布尔值 true。
password: 本应是字符串，但给出了整数 987654321。
created_at: 本应是日期时间格式，但给出了不正确的数字 20240101。
is_active: 本应是布尔类型，但给出了字符串 "yes"。
products:

product_id: 本应是整数，但给出了字符串 "101a"。
product_name: 本应是字符串，但给出了布尔值 false。
category: 本应是字符串，但给出了整数 123。
price: 本应是浮点数，但给出了字符串 "expensive"。
stock: 本应是整数，但给出了字符串 "a lot"。
created_at: 本应是有效的日期时间格式，但给出了字符串 "tomorrow"。
orders:

user_id: 本应是整数，但给出了字符串 "user_1"。
order_date: 本应是有效的日期时间格式，但给出了非标准格式 "15th March"。
total_amount: 本应是浮点数，但给出了字符串 "one thousand"。
status: 本应是字符串，但给出了整数 1234。
items.product_id: 本应是整数，但给出了布尔值 true。
items.quantity: 本应是整数，但给出了字符串 "one"。
items.price: 本应是浮点数，但给出了字符串 "cheap"。
reviews:

review_id: 本应是整数，但给出了字符串 "3001A"。
product_id: 本应是整数，但给出了布尔值 false。
user_id: 本应是整数，但给出了字符串 "user_1"。
rating: 本应是 1-5 的整数，但给出了字符串 "excellent"。
comment: 本应是字符串，但给出了整数 99999。
created_at: 本应是有效的日期时间格式，但给出了不正确的数字 20240318。
inventory:

product_id: 本应是整数，但给出了字符串 "ID101"。
stock_level: 本应是整数，但给出了字符串 "full"。
last_updated: 本应是有效的日期时间格式，但给出了字符串 "recently"。
