import time

import boto3
import pymysql
from aiohttp import ClientError
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import make_response, request

pymysql.install_as_MySQLdb()

app = Flask(__name__, static_url_path='')
# ------------------database----------------------------
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql://root:dbuserdbuser@e6156.ck7gj29hlh1f.us-east-1.rds.amazonaws.com:3306/store_product'
# 指定数据库文件
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# 允许修改跟踪数据库
db = SQLAlchemy(app)

class Products(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    category_id = db.Column(db.Integer)
    product_title = db.Column(db.Text)
    product_intro = db.Column(db.Text)
    product_picture = db.Column(db.String(200))
    product_price = db.Column(db.Numeric)
    product_selling_price = db.Column(db.Numeric)
    product_num = db.Column(db.Integer)
    product_sales = db.Column(db.Integer)
    category_name = db.Column(db.String(100))

class Pictures(db.Model):
    __tablename__ = 'product_picture'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    product_picture = db.Column(db.String(200))
    intro = db.Column(db.Text)

class Categories(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(20))

class Carousels(db.Model):
    __tablename__ = 'carousel'
    carousel_id = db.Column(db.Integer, primary_key=True)
    img_path = db.Column(db.String(200))
    describes = db.Column(db.String(50))
    product_id = db.Column(db.Integer)
    priority = db.Column(db.Integer)

class Carts(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    num = db.Column(db.Integer)

class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    product_num = db.Column(db.Integer)
    product_price = db.Column(db.Float)
    order_time = db.Column(db.Integer)


def create_order(user_id, products):
    order = Orders()
    order.user_id = user_id
    order.product_id = products['productID']
    order.product_num = products['num']
    order.product_price = products['price']
    order.order_time = int(time.time())
    order.order_id = int(str(user_id)+str(int(time.time())))
    db.session.add(order)
    db.session.commit()


def list_order(user_id):
    orders = Orders.query.filter_by(user_id=user_id).all()
    return orders


@app.route('/order/list', methods=['POST'])
def order_list():
    user_id = request.get_json().get('user_id')
    orders = list_order(user_id)
    data = []
    for order in orders:
        product_name = Products.query.get(order['product_id']).product_name
        product_picture = Products.query.get(order['product_id']).product_picture
        dict = {}
        dict['id'] = order.id
        dict['order_id'] = order.order_id
        dict['user_id'] = order.user_id
        dict['product_id'] = order.product_id
        dict['product_num'] = order.product_num
        dict['product_price'] = order.product_price
        dict['order_time'] = order.order_time
        dict['product_name'] = product_name
        dict['product_picture'] = product_picture
        data.append(dict)
    return {'code': '001', 'data': data}



@app.route('/order/save', methods=['POST'])
def order_save():
    user_id = request.get_json().get('user_id')
    products = request.get_json().get('products')
    for product in products:
        # 保存订单
        create_order(user_id, product)
        # 清除购物车
        delete_cart(user_id, product['productID'])
        # 修改库存和销售
        update_product_num_and_sales(product['productID'], product['num'])

    return {'code': '001', 'msg': 'purchase success!'}


def update_product_num_and_sales(product_id, num):
    product = Products.query.get(product_id)
    product.product_num -= num
    product.product_sales += num


def check_cart(user_id, product_id):
    carts = Carts.query.filter_by(user_id=user_id).filter_by(product_id=product_id).all()
    if len(carts) == 0:
        return True
    return False


def cart_add(user_id, product_id):
    cart = Carts()
    cart.user_id = user_id
    cart.product_id = product_id
    cart.num = 1
    db.session.add(cart)
    db.session.commit()


def update_cart_num_1(user_id, product_id):
    cart = Carts.query.filter_by(user_id=user_id).filter_by(product_id=product_id).first()
    max_num = Products.query.filter_by(product_id=product_id).first().product_num
    if cart.num >= max_num:
        return False
    cart.num += 1
    db.session.commit()
    return True


def update_cart_num(user_id, product_id, num):
    cart = Carts.query.filter_by(user_id=user_id).filter_by(product_id=product_id).first()
    max_num = Products.query.filter_by(product_id=product_id).first().product_num
    if num > max_num:
        return False
    cart.num = num
    db.session.commit()
    return True


def query_cart(user_id, product_id):
    cart = Carts.query.filter_by(user_id=user_id, product_id=product_id).first()
    return cart


def query_cart_by_user_id(user_id):
    carts = Carts.query.filter_by(user_id=user_id).all()
    return carts





@app.route('/cart/list', methods=['POST'])
def cart_list():
    # 查询用户对应的购物车数据
    # 查询购物车对应的商品数据
    # 进行数据封装
    # 返回结果即可
    user_id = request.get_json().get('user_id')
    carts = query_cart_by_user_id(user_id)
    cart_list = []
    for cart in carts:
        product_id = cart.product_id
        num = cart.num
        s = select_by_id(product_id)
        cart_id = query_cart(user_id, product_id).id
        dic = {}
        dic['id'] = cart_id
        dic['productID'] = s.product_id
        dic['productName'] = s.product_name
        dic['productImg'] = s.product_picture
        dic['price'] = s.product_selling_price
        dic['num'] = num
        dic['maxNum'] = s.product_num
        dic['check'] = False
        cart_list.append(dic)
    res = {'code': '001', 'data': cart_list}
    return res

def delete_cart(user_id, product_id):
    cart = Carts.query.filter_by(user_id=user_id).filter_by(product_id=product_id).first()
    db.session.delete(cart)
    db.session.commit()

@app.route('/cart/update', methods=['POST'])
def cart_update():
    product_id = request.get_json().get('product_id')
    user_id = request.get_json().get('user_id')
    num = request.get_json().get('num')
    status = update_cart_num(user_id, product_id, num)
    if not status:
        return {'code': '004', 'msg': 'number is larger than stock'}
    return {'code': '001', 'msg': 'modify number success!'}

@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    product_id = request.get_json().get('product_id')
    user_id = request.get_json().get('user_id')
    delete_cart(user_id, product_id)
    return {'code': '001', 'msg': 'remove cart success!'}


@app.route('/cart/save', methods=['POST'])
def cart_save():
    # 进行购物车数据保存
    # 初次保存，返回的数量为1
    # 非初次保存，返回002状态码即可，提示已经添加过，前端会自动化数量 + 1
    # 如果超出购物买数量，返回003！
    user_id = request.get_json().get('user_id')
    product_id = request.get_json().get('product_id')
    is_empty = check_cart(user_id, product_id)
    if is_empty:
        cart_add(user_id, product_id)
        s = select_by_id(product_id)
        cart_id = query_cart(user_id, product_id).id
        dic = {}
        dic['id'] = cart_id
        dic['productID'] = s.product_id
        dic['productName'] = s.product_name
        dic['productImg'] = s.product_picture
        dic['price'] = s.product_selling_price
        dic['num'] = 1
        dic['maxNum'] = s.product_num
        dic['check'] = False
        res = {'code': '001', 'data': dic, 'msg': 'add to cart success!'}
        return res
    else:
        status = update_cart_num_1(user_id, product_id)
        if status:
            return {'code': '002', 'msg': 'This product was in your cart, number + 1!'}
        else:
            return {'code': '003', 'msg': 'Can not add, stock is not enough!'}



# query all carousel data
def select_all():
    carousels = Carousels.query.all()
    carousels_list = []
    for carousel in carousels:
        dic = {}
        dic['carousel_id'] = carousel.carousel_id
        dic['img_path'] = carousel.img_path
        dic['describes'] = carousel.describes
        dic['product_id'] = carousel.product_id
        dic['priority'] = carousel.priority
        carousels_list.append(dic)
    return carousels_list

# 查询所有
def select_all_products():
    product_list = []
    products = Products.query.all()
    # 类似于 select * from Books
    for s in products:
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        product_list.append(dic)
    return product_list

def select_pictures_by_product_id(product_id):
    picture_list = []
    pictures = Pictures.query.filter_by(product_id=product_id).all()
    for s in pictures:
        dic = {}
        dic['id'] = s.id
        dic['product_id'] = s.product_id
        dic['product_picture'] = s.product_picture
        dic['intro'] = s.intro
        picture_list.append(dic)
    return picture_list

# 查询所有类别
def select_all_categories():
    category_list = []
    categories = Categories.query.all()
    for s in categories:
        dic = {}
        dic['category_id'] = s.category_id
        dic['category_name'] = s.category_name
        category_list.append(dic)
    return category_list

# 查询类别id
def select_id_by_name(category_name):
    pair = Categories.query.filter_by(category_name=category_name).first()
    return pair.category_id

# 按多类别查询
def select_all_by_categories(category_id):
    products = Products.query.filter(Products.category_id.in_(category_id)).all()
    return products

# 根据id查找
def select_by_id(product_id):
    product = Products.query.get(product_id)
    return product

# 首页类别
def select_7_by_category_name(category_name):
    products = Products.query.filter_by(category_name=category_name).order_by(-Products.product_sales).all()
    return products[0:min(7, len(products))]

# 首页热门
def select_7_by_category_names(category_names):
    products = Products.query.filter(Products.category_name.in_(category_names)).order_by(-Products.product_sales).all()
    return products[0:min(7, len(products))]

@app.route('/product/detail', methods=['POST'])
def query_by_id():
    product_id = request.get_json().get('productID')
    s = select_by_id(product_id)
    dic = {}
    dic['product_id'] = s.product_id
    dic['product_name'] = s.product_name
    dic['category_id'] = s.category_id
    dic['product_title'] = s.product_title
    dic['product_intro'] = s.product_intro
    dic['product_picture'] = s.product_picture
    dic['product_price'] = s.product_price
    dic['product_selling_price'] = s.product_selling_price
    dic['product_num'] = s.product_num
    dic['product_sales'] = s.product_sales
    dic['category_name'] = s.category_name
    res = {
        'code': '001',
        'data': dic
    }
    return res


@app.route('/product/detail', methods=['POST'])
def query_product_detail():
    id = request.get_json().get('productID')



@app.route('/product/bycategory', methods=['POST'])
def query_product_bycategory():
    req = request.get_json()
    category_ids = req.get('categoryID')
    current_page = req.get('currentPage')
    page_size = req.get('pageSize')
    products = select_all_by_categories(category_ids)
    total = len(products)
    products = products[(current_page - 1) * page_size: min(current_page * page_size, len(products))]

    product_list = []
    for s in products:
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        product_list.append(dic)

    response = {'code': '001'}
    response['data'] = product_list
    response['total'] = total
    return response



@app.route('/product/hots', methods=['POST'])
def query_7_hot():
    category_names = request.get_json().get('categoryName')
    products = select_7_by_category_names(category_names)
    product_list = []
    for s in products:
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        product_list.append(dic)
    res = {'code': '001',
           'data': product_list}
    return res

@app.route('/product/category/list', methods=['POST'])
def product_category_list():
    categories = select_all_categories()
    response = {"code": "001",
                'data': categories}
    return response

@app.route('/product/promo', methods=['POST'])
def query_7():
    category_name = request.get_json().get('categoryName')
    products = select_7_by_category_name(category_name)
    product_list = []
    for s in products:
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        product_list.append(dic)
    res = {'code': '001',
           'data': product_list}
    return res


@app.route('/category/list')
def query_all_categories():
    categories = select_all_categories()
    response = {"code": "001",
                'data': categories}
    return response

@app.route('/category/<categoryName>', methods=['GET'])
def query_category_by_name(categoryName):
    category_name = categoryName
    # category_name = request.get_json().get('categoryName')
    category_id = select_id_by_name(category_name)
    response = {"code":'001'}
    data = {'category_id':category_id,
            'category_name':category_name}
    response['data'] = data
    return response

@app.route('/category/names', methods=['POST'])
def multi_category():
    name_list = request.get_json().get('categoryName')
    id_list = []
    for name in name_list:
        id = select_id_by_name(name)
        id_list.append(id)
    response = {'code':'001',
                'data':id_list}
    return response


@app.route('/product/all', methods=['POST'])
def query_all():
    request_data = request.get_json()
    category_ids = request_data.get('categoryID')
    current_page = request_data.get('currentPage')
    page_size = request_data.get('pageSize')
    products = []
    if len(category_ids) == 0:
        products = Products.query.all()
    else:
        products = select_all_by_categories(category_ids)
    total = len(products)
    products = products[(current_page-1)*page_size: min(current_page*page_size, len(products))]

    product_list = []
    for s in products:
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        product_list.append(dic)

    response = {'code':'001'}
    response['data'] = product_list
    response['total'] = total
    return response

@app.route('/product/pictures', methods=['POST'])
def query_pictures():
    response = {'code': '001'}
    product_id = request.get_json().get('productID')
    pictures = select_pictures_by_product_id(product_id)
    response['data'] = pictures
    return response

@app.route('/carousel/list', methods=['POST'])
def query_carousel():
    data = select_all()
    res = {
        'code': '001',
        'data': data
    }
    return res

class Collects(db.Model):
    __tablename__ = 'collect'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    collect_time = db.Column(db.Integer)

def check_collect(product_id, user_id):
    lists = Collects.query.filter_by(product_id=product_id).filter_by(user_id=user_id).all()
    if len(lists) == 0:
        return True
    return False

def save_collect(product_id, user_id):
    collect = Collects()
    collect.user_id = user_id
    collect.product_id = product_id
    collect.collect_time = int(time.time())
    db.session.add(collect)
    db.session.commit()

def select_collect_by_user(user_id):
    collects = Collects.query.filter_by(user_id=user_id)
    return collects


@app.route('/collect/save', methods=['POST'])
def collect_save():
    product_id = request.get_json().get('product_id')
    user_id = request.get_json().get('user_id')

    # 判断是否存在收藏
    isCheck = check_collect(product_id, user_id)

    # 存在，提示对应的错误
    if not isCheck:
        res = {'code': '004', 'msg': 'You have collected this product!'}
        return res

    # 不存在，添加，并且提示添加成功即可
    save_collect(product_id, user_id)
    res = {'code': '001', 'msg': 'Collect Success!'}
    return res

@app.route('/collect/list', methods=['POST'])
def collect_list():
    user_id = request.get_json().get('user_id')
    collects = select_collect_by_user(user_id)

    collect_list = []
    for collect in collects:
        product_id = collect.product_id
        s = select_by_id(product_id)
        dic = {}
        dic['product_id'] = s.product_id
        dic['product_name'] = s.product_name
        dic['category_id'] = s.category_id
        dic['product_title'] = s.product_title
        dic['product_intro'] = s.product_intro
        dic['product_picture'] = s.product_picture
        dic['product_price'] = s.product_price
        dic['product_selling_price'] = s.product_selling_price
        dic['product_num'] = s.product_num
        dic['product_sales'] = s.product_sales
        dic['category_name'] = s.category_name
        collect_list.append(dic)

    res = {
        'code': '001',
        'data': collect_list
    }
    return res

def remove_collect_by_pair(user_id, product_id):
    collect = Collects.query.filter_by(user_id=user_id).filter_by(product_id=product_id).first()
    db.session.delete(collect)
    db.session.commit()


@app.route('/collect/remove', methods=['POST'])
def collect_remove():
    user_id = request.get_json().get('user_id')
    product_id = request.get_json().get('product_id')
    remove_collect_by_pair(user_id, product_id)
    res = {
        'code': '001',
        'msg': 'remove success!'
    }
    return res

@app.route('/feedback', methods=['POST'])
def send_email():
    feedback = request.get_json().get('msg')
    if len(feedback) == 0:
        return {'code': '004', 'msg':'bad'}

    sns_client = boto3.client('sns')
    topic_arn = "arn:aws:sns:us-east-1:964216032660:6156_to_lambda"
    # Publish to topic
    sns_client.publish(TopicArn=topic_arn,
                       Message=feedback,
                       Subject="Feedback from An User")
    return {'code': '001', 'msg':'send success!'}


if __name__ == '__main__':
    # 默认是5000，这里设置5001避免本地冲突。打开debug方便调试
    app.run(debug=True, port=5000)
