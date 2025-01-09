# Spider ZIP Package Usage Documentation

[Chinese](README_zh.md)

## Introduction

In the TSDAP platform, each spider is an independent entity imported into the platform as a ZIP package. Each spider package contains a `compose.json` file that describes the basic information and configuration of the spider. The main class of the spider needs to inherit the `ISpider` interface and implement its abstract methods.

## `compose.json` File Structure

The `compose.json` file contains the following sections:

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

### Field Descriptions

- `infos`: Contains basic information about the spider.
  - `name`: Name of the spider.
  - `tag`: Version of the spider.
  - `desc`: Description of the spider.
  - `author`: Author information.

- `runtimes`: Contains runtime configuration information for the spider.
  - `entry`: Entry file name of the spider.
  - `daemon`: Whether to run as a daemon process.
  - `envs`: Environment variables at runtime.
  - `dependencies`: List of Python packages that the spider depends on.

- `schedules`: Contains scheduling information for the spider.
  - `cron`: Scheduling time defined using a cron expression.

### Notes
  - The `daemon` option cannot be used simultaneously with the `cron` option.
  - The `cron` schedule will only be invoked if the spider exits normally.

## `ISpider` Interface

The main class of the spider needs to inherit the `ISpider` interface and implement its abstract methods. Below is the definition of the `ISpider` interface:

```python
class ISpider(ABC):
    """Each spider has a class that needs to inherit and implement abstract functions,
    the inherited class will serve as the entry point of the spider.
    """

    def __init__(self) -> None:
        self.logger: logging.Logger
        """Logger for the spider"""

    @abstractmethod
    def run(self) -> None:
        """Entry function of the spider, must be overridden"""
        pass

    @abstractmethod
    def unload(self) -> None:
      """Unload function of the spider, must be overridden"""
      pass
```

### Method Descriptions
- `run`: Entry function of the spider, similar to the main function, this function will serve as the key entry point for the platform to start the spider.
- `unload`: Unload function of the spider, when the platform sends a Stop request to the spider, this code will be automatically executed to save resources and perform cleanup tasks.

### Spider Packaging

The spider needs to be packaged in ZIP format. When packaging, ensure the following file and directory structure:

```
your_spider.zip
├── compose.json
└── your_spider/
  ├── __init__.py
  └── main.py
```

- `compose.json`: Describes the basic information and configuration of the spider.
- `your_spider/`: Directory containing the spider's code.
  - `__init__.py`: Initialization file.
  - `main.py`: Main entry file of the spider.

After packaging the above structure into a ZIP file, it can be imported into the TSDAP platform for execution. If packaged according to the above structure, the `entry` field in `compose.json` should be filled in as `your_spider/main`.
