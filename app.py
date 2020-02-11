from flask import Flask,render_template,request,redirect,url_for
import requests,json,re,logging
from flask_apscheduler import APScheduler
app = Flask(__name__)

#定时器设置
scheduler = APScheduler()
scheduler.init_app(app=app)
scheduler.start()

#日志设置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s - %(message)s',filename='output.log',
                    datefmt='%Y/%m/%d %H:%M:%S')
logger = logging.getLogger(__name__)


@app.route('/',methods=("GET", "POST"))
def main():
    if request.method == 'GET':
        return render_template('setting.html')
    if request.method == 'POST':
        Id = request.form.get('Id')
        if check_Id(Id) == -1:
            return "是不是账号输错啦w(ﾟДﾟ)w"
        user_ip = request.remote_addr
        logger.debug(user_ip+" 加入打卡列表，学号："+Id)
        return redirect(url_for('sign',Id=Id))


@app.route('/<int:Id>')
def sign(Id):
    idList = json.load(open('setting.json'))
    if Id in idList['Id']:
        return "已经在打卡列表中啦w(ﾟДﾟ)w"
    else:
        idList['Id'].append(Id)
        idList['num'] += 1
    json.dump(idList, open('setting.json', 'w'))
    return "加入打卡列表成功ヽ(✿ﾟ▽ﾟ)ノ"


"""
启动定时打卡
eg：访问127.0.0.1:5000/addTask/your-password
your-password设置在setting.json中
"""
@app.route('/addTask/<string:pw>')
def addTask(pw):
    #检测密码，密码在setting.json文件中设置
    setting = json.load(open('setting.json'))
    password = setting['password']
    hour = setting['startHour']
    minute = setting['startMin']
    if (password == "") or (hour == "") or (minute == ""):
        return "setting.json未设置相关参数"
    if pw == password:
        scheduler.add_job(func=task, id='start', trigger='cron', hour=hour, minute=minute)
        logger.info('任务开始')
        return "任务开始"
    else:
        return redirect(url_for('main'))


"""
停止定时打卡
eg：访问127.0.0.1:5000/removeTask/your-password
your-password设置在setting.json中
"""
@app.route('/removeTask/<string:pw>')
def removeTask(pw):
    setting = json.load(open('setting.json'))
    password = setting['password']
    if password == "":
        return "setting.json未设置相关参数"
    if pw == password:
        scheduler.remove_all_jobs()
        logger.info('任务结束')
        return "任务结束"
    else:
        return redirect(url_for('main'))

"""
网页端查看log
eg：访问127.0.0.1:5000/catLog/your-password
your-password设置在setting.json中
"""
@app.route('/catLog/<string:pw>')
def catLog(pw):
    setting = json.load(open('setting.json'))
    password = setting['password']
    if password == "":
        return "setting.json未设置相关参数"
    allLogpis = ""
    if pw == password:
        with open('output.log') as f:
            for index,logpis in enumerate(f.readlines()):
                if index >= 10:
                    break
                allLogpis += (logpis +'<br/>')
        return allLogpis
    else:
        return redirect(url_for('main'))



"""
对setting.json中Id列表每一学号进行打卡任务
"""
def task():
    idList = json.load(open('setting.json'))
    for i in idList['Id']:
        logger.info(str(i)+'开始打卡')
        _sign(i)




"""
对单一学号进行打卡任务
"""
def _sign(Id):
    # url
    urlMd5 = "http://202.201.13.180:9037/encryption/getMD5"
    urlInfo = "http://202.201.13.180:9037/grtbMrsb/getInfo"
    urlSign = "http://202.201.13.180:9037/grtbMrsb/submit"

    parms = {'cardId': Id}
    try:
        res = requests.post(url=urlMd5, params=parms).json()
        md5 = res['data']
    except BaseException:
        logger.error(str(Id)+"获取Md5出错！打卡中止！")
        return


    parms = {'cardId': Id, 'md5': md5}
    try:
        res = requests.post(url=urlInfo, params=parms).json()
        data = res['data'][0]
    except BaseException:
        logger.error(str(Id)+"获取bh出错！打卡中止！")
        return


    parms = {'bh': data['bh'], 'xykh': data['xykh'], "twfw": 0, "sfzx": '0', "sfgl": '0', "szsf": data['szsf'],
             "szds": data['szds'],"szxq": data['szxq'], "sfcg": '0', "bllb": '0', "sfjctr": '0', "sbr": data["xm"]}
    # 这里要将字典转化为Json的格式，Json=可以自动将字典转化为json格式
    try:
        res = requests.post(url=urlSign, json=parms).json()
        logger.debug(res)
    except BaseException:
        logger.error(str(Id)+"打卡过程中止！")
        return
    logger.info(str(Id) + '结束打卡')

"""
检查学号合法性
"""
def check_Id(Id):
    pa = re.compile("^\d{12}$")
    #账号匹配失败
    if pa.match(str(Id)) == None:
        return -1
    else:
        return 0



if __name__ == '__main__':
    #app.config['SCHEDULER_API_ENABLED'] = True
    logger.info('程序启动')
    app.run()


