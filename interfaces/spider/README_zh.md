# 爬虫 ZIP 包使用文档

[English](README.md)

## 简介

在 TSDAP 平台中，每一个爬虫都是一个独立的个体，以 ZIP 包的形式导入到平台中。每个爬虫包包含一个 `compose.json` 文件，用于描述爬虫的基本信息和配置。爬虫的主类需要继承 `ISpider` 接口，并实现其抽象方法。

## `compose.json` 文件结构

`compose.json` 文件包含以下几个部分：

```json
{
    "infos": {
        "name": "test_spider",
        "tag": "1.0",
        "desc": "Just a test_spider",
        "author": "慕璃muri"
    },
    "runtimes": {
        "entry": "test_spider",
        "daemon": true,
        "envs": {"Name": "Value"},
        "dependencies": ["requests"]
    },
    "schedules": {
        "cron": "0 0 * * * *"
    }
}
```

### 字段说明

- `infos`: 包含爬虫的基本信息。
  - `name`: 爬虫名称。
  - `tag`: 爬虫版本。
  - `desc`: 爬虫描述。
  - `author`: 作者信息。

- `runtimes`: 包含爬虫运行时的配置信息。
  - `entry`: 爬虫的入口文件名。
  - `daemon`: 是否以守护进程方式运行。
  - `envs`: 运行时的环境变量。
  - `dependencies`: 爬虫依赖的 Python 包列表。

- `schedules`: 包含爬虫的调度信息。
  - `cron`: 使用 cron 表达式定义的调度时间。

### 注意事项
  - `daemon` 选项不能与 `cron` 选项同时使用。
  - `cron` 调度仅在爬虫正常退出的情况下才会调用。

## `ISpider` 接口

爬虫的主类需要继承 `ISpider` 接口，并实现其抽象方法。以下是 `ISpider` 接口的定义：

```python
class ISpider(ABC):
    """每个爬虫都有一个类需要继承并实现抽象函数，
    继承的类将作为爬虫的入口点。
    """

    def __init__(self) -> None:
        self.logger: logging.Logger
        """爬虫的日志记录器"""

    @abstractmethod
    def run(self) -> None:
        """爬虫的入口函数，必须重写"""
        pass

    @abstractmethod
    def unload(self) -> None:
      """爬虫的卸载函数，必须重写"""
      pass
```

### 方法说明
- `run`: 爬虫的入口函数, 如 main 函数一般, 该函数将作为平台启动爬虫的关键入口函数。
- `unload`: 爬虫的卸载函数, 当平台向爬虫发出Stop请求后, 将自动执行此处代码, 进行爬虫资源的保存, 清理等工作。
### 爬虫打包

爬虫需要通过 ZIP 格式进行打包。打包时，请确保以下文件和目录结构：

```
your_spider.zip
├── compose.json
└── your_spider/
  ├── __init__.py
  └── main.py
```

- `compose.json`: 描述爬虫的基本信息和配置。
- `your_spider/`: 爬虫的代码目录。
  - `__init__.py`: 初始化文件。
  - `main.py`: 爬虫的主入口文件。

将上述结构打包成 ZIP 文件后，即可将其导入到 TSDAP 平台中进行运行。
若按照上述结构打包, 则`compose.json`中`entry`字段将填写为`your_spider/main`
