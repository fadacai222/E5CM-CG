import os


def 获取项目根目录() -> str:
    # core 在 项目根目录/core，所以上一层就是根
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def 拼路径(*片段) -> str:
    return os.path.join(获取项目根目录(), *片段)


def 默认资源路径():
    根 = 获取项目根目录()
    return {
        # 背景（旧的图片背景，新的已经使用视频替代）
        "背景_玩家": 拼路径("冷资源", "backimages", "b_scene_screen.png"),
        "背景_模式": 拼路径("冷资源", "backimages", "scene2.jpg"),
        "背景_子模式": 拼路径("冷资源", "backimages", "scene3.jpg"),
        # 模式按钮图
        "图_花式": 拼路径("UI-img", "大模式选择界面", "按钮", "花式模式按钮.png"),
        "图_竞速": 拼路径("UI-img", "大模式选择界面", "按钮", "竞速模式按钮.png"),
        "图_疯狂": 拼路径("UI-img", "玩法选择界面", "按钮", "疯狂模式按钮.png"),
        "图_混音": 拼路径("UI-img", "玩法选择界面", "按钮", "混音模式按钮.png"),
        "图_表演候选": [
            拼路径("UI-img", "玩法选择界面", "按钮", "表演模式按钮.png"),
            拼路径("UI-img", "玩法选择界面", "按钮", "花式表演按钮.png"),
            拼路径("UI-img", "玩法选择界面", "按钮", "竞速表演按钮.png"),
        ],
        "图_club候选": [
            拼路径("UI-img", "玩法选择界面", "按钮", "club模式按钮.png"),
            拼路径("UI-img", "玩法选择界面", "按钮", "花式club按钮.png"),
            拼路径("UI-img", "玩法选择界面", "按钮", "竞速club按钮.png"),
        ],
        # 音乐（旧的）
        "音乐_开始": 拼路径("冷资源", "backsound", "back_music_logo.mp3"),
        "音乐_UI": 拼路径("冷资源", "backsound", "back_music_ui.mp3"),
        "音乐_show": 拼路径("冷资源", "backsound", "show.mp3"),
        "音乐_devil": 拼路径("冷资源", "backsound", "devil.mp3"),
        "音乐_remix": 拼路径("冷资源", "backsound", "remix.mp3"),
        "音乐_club": 拼路径("冷资源", "backsound", "club.mp3"),
        # ========== 投币/1P2P 公共（与上一步一致） ==========
        "backmovies目录": 拼路径("backmovies"),
        # 指定只播一个视频；留空则选 backmovies 排序第一个
        "投币_背景视频": "",
        "投币_遮罩": 拼路径("冷资源", "backimages", "50%黑色遮罩.png"),
        "投币_BGM": 拼路径("冷资源", "backsound", "back_music_logo.mp3"),
        "投币_logo": 拼路径("UI-img", "拼贴banner", "大logo.png"),
        "投币_联网图标": 拼路径("UI-img", "联网状态", "已联网.png"),
        # 投币按钮
        "投币_按钮": 拼路径("UI-img", "投币界面", "投币按钮.png"),
        # ✅ 1P2P 按钮
        "1P按钮": 拼路径("UI-img", "玩家选择界面", "1P.png"),
        "2P按钮": 拼路径("UI-img", "玩家选择界面", "2P.png"),
        # ===== 登陆界面资源 =====
        "登陆_top背景": 拼路径("UI-img", "top栏", "top栏背景.png"),
        "登陆_个人中心": 拼路径("UI-img", "top栏", "个人中心.png"),
        "登陆_场景1_游客": 拼路径("UI-img", "个人中心-登陆", "场景1-游客.png"),
        "登陆_场景1_vip半透明": 拼路径(
            "UI-img", "个人中心-登陆", "场景1-vip磁卡-半透明.png"
        ),
        "登陆_场景2_游客": 拼路径("UI-img", "个人中心-登陆", "场景2-游客.png"),
        "登陆_请刷卡背景": 拼路径("UI-img", "个人中心-登陆", "请刷卡背景.png"),
        "登陆_请刷卡内容": 拼路径("UI-img", "个人中心-登陆", "请刷卡内容.png"),
        "登陆_请刷卡内容白": 拼路径("UI-img", "个人中心-登陆", "请刷卡内容白色.png"),
        "登陆_磁卡": 拼路径("UI-img", "个人中心-登陆", "磁卡.png"),
        # ✅ 全局按钮音效
        "按钮音效": 拼路径("冷资源", "Buttonsound", "点击-增益5.mp3"),
        "投币音效": 拼路径("冷资源", "Buttonsound", "投币.mp3"),
        "刷卡音效": 拼路径("冷资源", "Buttonsound", "刷卡+5.mp3"),
        "根": 根,
    }
