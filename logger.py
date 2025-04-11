import logging
import warnings
import os
class logger():
    def __init__(self, name="log", path=".", filemode="a", format="%(asctime)s - %(levelname)s \t %(message)s", console_level="INFO", file_level="INFO"):
        self.__levels = {"NOTSET":0, "DEBUG":10, "INFO":20, "WARNING":30, "ERROR":40, "CRITICAL":50}
        self.__name = name
        self.__path = path
        self.__format = format
        self.__formatter = logging.Formatter(self.__format)
        self.__filemode = filemode
        self.__console_level = console_level
        self.__file_level = file_level
        self.__logger = logging.getLogger(name)
        if self.__console_level:
            self.__createHandler("console", self.__console_level)
        if self.__file_level:
            self.__createHandler("file", self.__file_level)
        self.setLevel()
    def __createHandler(self, destination, level):
        if destination == "console":
            handler = logging.StreamHandler()
            handler.setFormatter(self.__formatter)
            handler.setLevel(level)
            self.__logger.addHandler(handler)
        elif destination == "file":
            handler = logging.FileHandler(filename = os.path.join(self.__path, self.__name+".log"), mode = self.__filemode)
            handler.setFormatter(self.__formatter)
            handler.setLevel(level)
            self.__logger.addHandler(handler)
        else:
            raise ValueError("Handler type '%s' not implemented"%type)
    def __call__(self, message, level="info"):
        if level.upper() not in self.__levels:
            raise ValueError("Level '%s' not implemented"%level)
        getattr(self.__logger,level)(self.__checkmessage(message))
    def setName(self, name):
        self.__name = name
    def getName(self):
        return self.__name
    def getFile(self):
        if self.__file:
            return self.__name+".log"
        else:
            print("The logger is not saving to a file")
    def setLevel(self, level="DEBUG"):
        level = level.upper()
        if level not in self.__levels:
            raise ValueError("Level '%s' not implemented"%level)
        self.__logger.setLevel(getattr(logging,level))
    def getLevel(self):
        level = self.__logger.getEffectiveLevel()
        print(list(self.__levels.keys())[list(self.__levels.values()).index(level)])
    def __checkmessage(self,message):
        if message == "":
            warnings.warn("Your message is empty")
        else:
            return message
    def setFileMode(self, mode):
        if mode not in ["a","w"]:
            raise ValueError("File mode '%s' not implemented"%mode)
        self.__filemode = mode
    def getFileMode(self):
        return self.__filemode
    def setFormat(self, format):
        self.__formatter = logging.Formatter(format)
    def getFormat(self):
        return self.__format
    def setDateFormat(self, datefmt):
        pass
    def getDateFormat(self):
        pass
